# =============================================================================
#  analisis_kpi.R
#  Analítica Avanzada de Operaciones — Empresa de Servicios Lingüísticos
#  Descripción: Conecta a la BD SQLite, calcula KPIs logísticos y exporta
#               un reporte visual gerencial de alta calidad en PNG.
#
#  PAQUETES REQUERIDOS (instalar una sola vez en RStudio):
#    install.packages(c("DBI", "RSQLite", "dplyr", "lubridate",
#                       "ggplot2", "patchwork", "scales",
#                       "ggtext", "showtext", "sysfonts", "glue"))
# =============================================================================

suppressPackageStartupMessages({
  library(DBI)
  library(RSQLite)
  library(dplyr)
  library(lubridate)
  library(ggplot2)
  library(patchwork)
  library(scales)
  library(ggtext)
  library(showtext)
  library(sysfonts)
  library(glue)
})

# Fuentes tipograficas
font_add_google("Syne",    family = "syne")
font_add_google("DM Mono", family = "dm_mono")
showtext_auto()
showtext_opts(dpi = 300)

# Paleta corporativa
PAL <- list(
  bg      = "#0B0E13", surface = "#111620", card    = "#161C28",
  border  = "#1E2738", amber   = "#F0A500", emerald = "#00C48C",
  sky     = "#38BDF8", rose    = "#FB7185", violet  = "#A78BFA",
  text    = "#C8D3E8", muted   = "#5A6A8A"
)

pal_clientes <- c(
  "Cavelier Abogados S.A.S."    = "#F0A500",
  "Laboratorios Lafrancol S.A." = "#38BDF8",
  "Fundación Alianza por la Paz" = "#00C48C"
)

pal_puntualidad <- c(
  "A tiempo"  = "#00C48C",
  "Retrasado" = "#FB7185",
  "Cancelado" = "#5A6A8A"
)

# Conexion a SQLite
DB_PATH <- file.path("instance", "linguistic_mvp.db")
if (!file.exists(DB_PATH)) stop(glue("BD no encontrada: {DB_PATH}"))
con <- dbConnect(SQLite(), dbname = DB_PATH)
on.exit(dbDisconnect(con), add = TRUE)

raw_proyectos  <- dbReadTable(con, "proyectos")
raw_clientes   <- dbReadTable(con, "clientes")
raw_linguistas <- dbReadTable(con, "linguistas")

cat(glue("Proyectos cargados: {nrow(raw_proyectos)} | Clientes: {nrow(raw_clientes)} | Linguistas: {nrow(raw_linguistas)}\n\n"))

# Transformacion
proyectos <- raw_proyectos %>%
  left_join(raw_clientes   %>% select(id, nombre_cliente   = nombre), by = c("cliente_id"   = "id")) %>%
  left_join(raw_linguistas %>% select(id, nombre_linguista = nombre), by = c("linguista_id" = "id")) %>%
  mutate(
    creado_en      = ymd_hms(creado_en,      quiet = TRUE),
    actualizado_en = ymd_hms(actualizado_en, quiet = TRUE),
    deadline       = ymd_hms(deadline,       quiet = TRUE),
    costo_total    = as.numeric(costo_total),
    volumen        = as.numeric(volumen),
    dias_ciclo     = as.numeric(difftime(actualizado_en, creado_en, units = "days")),
    puntualidad    = case_when(
      estado == "cancelado"                              ~ "Cancelado",
      estado %in% c("recibido","en_proceso","revision") ~ "En curso",
      !is.na(deadline) & actualizado_en > deadline      ~ "Retrasado",
      TRUE                                               ~ "A tiempo"
    )
  )

cerrados     <- proyectos %>% filter(estado %in% c("entregado","facturado","cancelado"))
con_deadline <- proyectos %>% filter(!is.na(deadline), estado != "en_proceso")

# KPIs consola
kpi_activos    <- proyectos %>% filter(estado %in% c("recibido","en_proceso","revision")) %>% nrow()
kpi_entregados <- proyectos %>% filter(estado %in% c("entregado","facturado")) %>% nrow()
kpi_monto      <- sum(proyectos$costo_total, na.rm = TRUE)
kpi_ciclo_med  <- median(cerrados$dias_ciclo, na.rm = TRUE)
tasa_puntual   <- con_deadline %>% filter(puntualidad != "En curso") %>%
                    summarise(t = mean(puntualidad == "A tiempo")) %>% pull(t)

cat("── KPIs Operacionales ──────────────────────────────\n")
cat(glue("   Activos:         {kpi_activos}\n"))
cat(glue("   Entregados:      {kpi_entregados}\n"))
cat(glue("   Monto total:     USD ${format(round(kpi_monto), big.mark=',')}\n"))
cat(glue("   Ciclo mediano:   {round(kpi_ciclo_med,1)} dias\n"))
cat(glue("   Tasa puntual:    {percent(tasa_puntual,accuracy=1)}\n\n"))

# Ciclo por servicio
ciclo_servicio <- cerrados %>%
  filter(!is.na(dias_ciclo), dias_ciclo >= 0) %>%
  group_by(servicio) %>%
  summarise(dias_promedio = mean(dias_ciclo), dias_mediana = median(dias_ciclo),
            n = n(), .groups = "drop") %>% arrange(dias_promedio)
cat("── Tiempo promedio por servicio ─────────────────────\n"); print(as.data.frame(ciclo_servicio)); cat("\n")

# Tema corporativo
tema_ops <- theme_void() +
  theme(
    plot.background    = element_rect(fill = PAL$bg,      color = NA),
    panel.background   = element_rect(fill = PAL$surface,  color = NA),
    panel.border       = element_rect(fill = NA, color = PAL$border, linewidth = 0.5),
    panel.grid.major.y = element_line(color = PAL$border, linewidth = 0.3, linetype = "dashed"),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    axis.text.x        = element_text(family = "dm_mono", color = PAL$muted, size = 7.5),
    axis.text.y        = element_text(family = "dm_mono", color = PAL$muted, size = 7.5, hjust = 1),
    axis.title.x       = element_text(family = "syne",    color = PAL$muted, size = 8,  margin = margin(t = 6)),
    axis.title.y       = element_text(family = "syne",    color = PAL$muted, size = 8,  margin = margin(r = 8), angle = 90),
    axis.ticks         = element_blank(),
    plot.title         = element_markdown(family = "syne",    color = PAL$text,  size = 11, face = "bold", margin = margin(b = 4)),
    plot.subtitle      = element_markdown(family = "dm_mono", color = PAL$muted, size = 7.5, margin = margin(b = 10)),
    plot.margin        = margin(14, 14, 14, 14),
    legend.position    = "right",
    legend.direction   = "vertical",
    legend.background  = element_rect(fill = PAL$bg, color = NA),
    legend.title       = element_text(family = "syne",    color = PAL$muted, size = 7),
    legend.text        = element_text(family = "dm_mono", color = PAL$text,  size = 7),
    legend.key         = element_rect(fill = NA, color = NA),
    legend.key.size    = unit(0.35, "cm"),
    legend.margin      = margin(t = 6)
  )

pal_estados <- c(
  "Facturado"   = "#A78BFA",
  "Entregado"   = "#00C48C",
  "En revision" = "#F0A500",
  "En proceso"  = "#38BDF8",
  "Recibido"    = "#2A3347",
  "Cancelado"   = "#5A6A8A"
)

# PANEL A: Rendimiento financiero por cliente
fin_cliente <- proyectos %>%
  filter(!is.na(costo_total)) %>%
  group_by(nombre_cliente, estado) %>%
  summarise(monto = sum(costo_total, na.rm = TRUE), .groups = "drop") %>%
  mutate(
    estado_label = case_when(
      estado == "facturado"  ~ "Facturado",
      estado == "entregado"  ~ "Entregado",
      estado == "revision"   ~ "En revision",
      estado == "en_proceso" ~ "En proceso",
      estado == "recibido"   ~ "Recibido",
      estado == "cancelado"  ~ "Cancelado",
      TRUE ~ estado
    ),
    estado_label   = factor(estado_label, levels = c("Facturado","Entregado","En revision","En proceso","Recibido","Cancelado")),
    nombre_cliente = factor(nombre_cliente, levels = names(pal_clientes))
  )

total_cliente <- fin_cliente %>% group_by(nombre_cliente) %>% summarise(total = sum(monto), .groups = "drop")

etiq_clientes <- c(
  "Cavelier Abogados S.A.S."    = "Cavelier\nAbogados",
  "Laboratorios Lafrancol S.A." = "Lafrancol",
  "Fundación Alianza por la Paz" = "Alianza\npor la Paz"
)

p_financiero <- ggplot(fin_cliente, aes(x = nombre_cliente, y = monto, fill = estado_label)) +
  geom_col(width = 0.55, position = "stack") +
  geom_text(data = total_cliente,
            aes(x = nombre_cliente, y = total,
                label = glue("USD ${comma(total, accuracy=1)}")),
            inherit.aes = FALSE, vjust = -0.7, size = 2.8,
            family = "dm_mono", color = PAL$amber, fontface = "bold") +
  scale_fill_manual(values = pal_estados, name = "Estado") +
  scale_y_continuous(labels = label_dollar(prefix = "USD $", big.mark = ","),
                     expand = expansion(mult = c(0, 0.18))) +
  scale_x_discrete(labels = etiq_clientes) +
  labs(title = "**Rendimiento Financiero** por Cliente",
       subtitle = "Monto acumulado (USD) segmentado por estado logistico",
       x = NULL, y = "Monto total (USD)") +
  tema_ops

# PANEL B: Puntualidad por cliente
puntualidad_cliente <- con_deadline %>%
  filter(puntualidad != "En curso") %>%
  group_by(nombre_cliente, puntualidad) %>%
  summarise(n = n(), .groups = "drop") %>%
  group_by(nombre_cliente) %>%
  mutate(total = sum(n), pct = n / total,
         puntualidad = factor(puntualidad, levels = c("A tiempo","Retrasado","Cancelado"))) %>%
  ungroup() %>%
  mutate(nombre_cliente = factor(nombre_cliente, levels = names(pal_clientes)))

p_puntualidad <- ggplot(puntualidad_cliente,
                        aes(x = nombre_cliente, y = pct, fill = puntualidad)) +
  geom_col(width = 0.5, position = "stack") +
  geom_text(aes(label = ifelse(pct >= 0.10, percent(pct, accuracy = 1), "")),
            position = position_stack(vjust = 0.5),
            size = 2.8, family = "dm_mono", color = PAL$bg, fontface = "bold") +
  scale_fill_manual(values = pal_puntualidad, name = "Puntualidad") +
  scale_y_continuous(labels = label_percent(), expand = expansion(mult = c(0, 0.04))) +
  scale_x_discrete(labels = etiq_clientes) +
  labs(title = "**Cumplimiento de Deadline** por Cliente",
       subtitle = "Distribucion porcentual — proyectos cerrados con fecha limite",
       x = NULL, y = "Proporcion de proyectos") +
  tema_ops

# PANEL C: Ciclo de entrega por servicio
ciclo_detalle <- cerrados %>%
  filter(!is.na(dias_ciclo), dias_ciclo >= 0) %>%
  mutate(puntualidad = factor(puntualidad, levels = c("A tiempo","Retrasado","Cancelado")))

ciclo_stats <- ciclo_detalle %>%
  group_by(servicio) %>%
  summarise(mediana = median(dias_ciclo), q1 = quantile(dias_ciclo, 0.25),
            q3 = quantile(dias_ciclo, 0.75), .groups = "drop") %>%
  arrange(mediana) %>%
  mutate(servicio = factor(servicio, levels = servicio))

ciclo_detalle <- ciclo_detalle %>%
  mutate(servicio = factor(servicio, levels = levels(ciclo_stats$servicio)))

p_ciclo <- ggplot() +
  geom_linerange(data = ciclo_stats,
                 aes(x = servicio, ymin = q1, ymax = q3),
                 color = PAL$border, linewidth = 5, alpha = 0.9) +
  geom_jitter(data = ciclo_detalle,
              aes(x = servicio, y = dias_ciclo, color = puntualidad),
              width = 0.18, size = 2.4, alpha = 0.85) +
  geom_point(data = ciclo_stats,
             aes(x = servicio, y = mediana),
             shape = 18, size = 5, color = PAL$amber) +
  geom_text(data = ciclo_stats,
            aes(x = servicio, y = mediana,
                label = glue("{round(mediana,1)}d")),
            vjust = -1, size = 2.6, family = "dm_mono",
            color = PAL$amber, fontface = "bold") +
  scale_color_manual(values = pal_puntualidad, name = "Puntualidad") +
  scale_y_continuous(breaks = pretty_breaks(n = 5),
                     expand = expansion(mult = c(0.1, 0.2))) +
  coord_flip() +
  labs(title = "**Ciclo de Entrega** por Tipo de Servicio",
       subtitle = "Mediana (diamante) e IQR (barra) · puntos = proyectos individuales",
       x = NULL, y = "Dias desde creacion hasta cierre") +
  tema_ops +
  theme(panel.grid.major.y = element_blank(),
        panel.grid.major.x = element_line(color = PAL$border, linewidth = 0.3, linetype = "dashed"))

# PANEL D: Volumen vs. costo (scatter)
scatter_df <- proyectos %>%
  filter(!is.na(volumen), !is.na(costo_total), estado != "cancelado") %>%
  mutate(
    unidad         = ifelse(grepl("nterpret", servicio), "horas", "palabras"),
    nombre_cliente = factor(nombre_cliente, levels = names(pal_clientes))
  )

p_scatter <- ggplot(scatter_df, aes(x = volumen, y = costo_total, color = nombre_cliente)) +
  geom_smooth(method = "lm", se = FALSE, linewidth = 0.6, alpha = 0.4, linetype = "dashed") +
  geom_point(aes(shape = unidad), size = 3, alpha = 0.9) +
  geom_text(aes(label = codigo_seguimiento),
            vjust = -1, size = 2.1, family = "dm_mono", alpha = 0.7) +
  scale_color_manual(values = pal_clientes, name = "Cliente") +
  scale_shape_manual(values = c("palabras" = 16, "horas" = 17), name = "Unidad") +
  scale_x_continuous(labels = label_comma(), expand = expansion(mult = c(0.05, 0.12))) +
  scale_y_continuous(labels = label_dollar(prefix = "USD $"),
                     expand = expansion(mult = c(0.1, 0.15))) +
  labs(title = "**Volumen vs. Costo** por Proyecto",
       subtitle = "Cada punto = 1 proyecto · linea punteada = tendencia lineal por cliente",
       x = "Volumen (palabras / horas)", y = "Costo total (USD)") +
  tema_ops

# CABECERA KPI cards
kpi_labels <- data.frame(
  x         = c(1, 2, 3, 4, 5),
  valor     = c(glue("{kpi_activos}"),
                glue("{kpi_entregados}"),
                glue("USD ${format(round(kpi_monto), big.mark=',')}"),
                glue("{percent(tasa_puntual, accuracy=1)}"),
                glue("{round(kpi_ciclo_med,1)} dias")),
  etiq      = c("PROYECTOS\nACTIVOS","ENTREGADOS\nY FACTURADOS",
                "MONTO TOTAL\nPORTAFOLIO","TASA DE\nPUNTUALIDAD",
                "CICLO MEDIANO\nDE ENTREGA"),
  color_val = c("#38BDF8","#00C48C","#F0A500","#00C48C","#F0A500")
)

p_header <- ggplot(kpi_labels, aes(x = x)) +
  geom_tile(aes(y = 0), width = 0.88, height = 2.0,
            fill = PAL$card, color = PAL$border, linewidth = 0.4) +
  geom_text(aes(y = 0.35, label = valor, color = color_val),
            size = 4.8, family = "syne", fontface = "bold") +
  geom_text(aes(y = -0.45, label = etiq, color = I(PAL$muted)),
            size = 2.3, family = "dm_mono", lineheight = 1.1) +
  scale_color_identity() +
  scale_x_continuous(limits = c(0.4, 5.6)) +
  scale_y_continuous(limits = c(-1.2, 1.2)) +
  theme_void() +
  theme(plot.background = element_rect(fill = PAL$bg, color = NA),
        plot.margin = margin(4, 14, 4, 14))

# Ensamblaje con patchwork
reporte_final <- (
  p_header /
  (p_financiero | p_puntualidad) /
  (p_ciclo | p_scatter)
) +
  plot_annotation(
    title    = "REPORTE SEMANAL DE OPERACIONES LINGUISTICAS",
    subtitle = glue("Generado automaticamente · {format(Sys.time(), '%d de %B de %Y, %H:%M')} · ",
                    "Base: {nrow(proyectos)} proyectos · {nrow(raw_clientes)} clientes · ",
                    "{nrow(raw_linguistas)} linguistas"),
    caption  = "Gestor Lingüístico · Centro de Analítica de Operaciones · Uso interno — Confidencial",
    theme    = theme(
      plot.background = element_rect(fill = PAL$bg, color = NA),
      plot.title      = element_text(family = "syne",    color = PAL$text,  size = 15, face = "bold",
                                     margin = margin(b = 2, t = 8, l = 8)),
      plot.subtitle   = element_text(family = "dm_mono", color = PAL$muted, size = 8,
                                     margin = margin(b = 12, l = 8)),
      plot.caption    = element_text(family = "dm_mono", color = PAL$border, size = 6.5,
                                     margin = margin(t = 10, b = 6, r = 8), hjust = 1)
    )
  ) +
  plot_layout(heights = c(0.18, 0.42, 0.40))

# Exportar
OUTPUT_FILE <- "reporte_operaciones.png"
ggsave(filename = OUTPUT_FILE, plot = reporte_final,
       width = 16, height = 11, dpi = 300, bg = PAL$bg)

cat(glue("── Reporte exportado ────────────────────────────────────────────\n"))
cat(glue("   Archivo:  {OUTPUT_FILE}\n"))
cat(glue("   Tamano:   {round(file.size(OUTPUT_FILE)/1024)} KB\n"))
cat(glue("   Ruta:     {normalizePath(OUTPUT_FILE)}\n"))
cat("Listo para adjuntar en el reporte gerencial semanal.\n")
