# Dashboard layout improvements

## Goal
Apply the provided UX spec to `templates/dashboard.html` and `static/css/dashboard.css`.

## Tasks
1. KPI cards in one 4-column row (grid-template-columns: repeat(4, 1fr)).
2. Below KPIs: 2 columns (60% bar chart, 40% "Actividad Reciente" panel).
3. Work area background #F4F7F5; individual white cards with subtle shadow for indicators, chart, notices.
4. KPI colors: Usuarios #1E88A8, Servicios Activos #1B7A43, Recaudo Julio #2E8B57/#D9A441, PQRS #E05A47 (left border or icon).
5. Topbar badge: background #E8F3EE, text #14532D.

## Validation
- Run app, view dashboard, confirm layout and colors.
- Lint/typecheck if available.

## Open questions
- None.si 

# Vibrant Organic & Glassmorphic Redesign (Zero Flat White) — VeredalApp Dashboard

## Goal
Transform `templates/dashboard.html` and `static/css/dashboard.css` into a vibrant, non-traditional, modern community water dashboard. Eliminate ALL flat white (`#FFFFFF`) backgrounds across the header, workspace, containers, and cards—replacing them with rich multi-tone green/water gradients, subtle topographic/wave SVG patterns, and frosted green-tinted glass panels.

## Tasks
1. **Vibrant Top Header with Wave Pattern (`static/css/dashboard.css` & `templates/dashboard.html`)**:
   - Replace the white top bar with a bold, lively gradient (`linear-gradient(120deg, #0B3B2B 0%, #156B4B 50%, #167D8C 100%)`) layered with an inline SVG pattern of flowing water waves and botanical curves (`opacity: 0.12`).
   - Place the circular logo inside a glowing warm-cream/mint ring (`background: linear-gradient(135deg, #F3EFE4, #DDF2E8); border-radius: 50%; padding: 4px; box-shadow: 0 0 15px rgba(255,255,255,0.25);`).
   - Style the title ("VeredalApp") in `#F5F2E8` and subtitle in `#B7EBD6`.

2. **Lively Patterned Main Canvas (`static/css/dashboard.css`)**:
   - Replace the flat gray/white workspace background with a rich multi-stop gradient (`linear-gradient(145deg, #B8DFCE 0%, #CBE8DF 45%, #B9DCE6 100%)`) overlaid with an inline SVG topographic contour & water-ripple pattern (`background-repeat: repeat`, subtle forest green lines at `0.09` opacity) so the entire page feels alive and rooted in rural water management.

3. **Frosted Tinted Glass Containers & Gradient KPI Cards (Zero White Blocks)**:
   - **Outer section panels** ("Dashboard Principal — Resumen Comunitario" and bottom chart/activity wrapper): Replace white boxes with frosted mint-tinted glass (`background: linear-gradient(135deg, rgba(226, 245, 236, 0.78), rgba(212, 238, 232, 0.68)); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.55); box-shadow: 0 8px 24px rgba(15, 61, 46, 0.08);`).
   - **KPI Cards** (`USUARIOS`, `SERVICIOS ACTIVOS`, `RECAUDO JULIO`, `PQRS PENDIENTES`): Give each card a distinct soft gradient background with a decorative SVG wave/leaf accent in the bottom-right corner and bold left border:
     - Usuarios: `linear-gradient(135deg, #D8EFF6 0%, #E7F5F9 100%)`, accent `#1E88A8`
     - Servicios Activos: `linear-gradient(135deg, #D5EFE2 0%, #E6F6EE 100%)`, accent `#1B7A43`
     - Recaudo Julio: `linear-gradient(135deg, #E3EED6 0%, #F2F5E4 100%)`, accent `#5D8A2F`
     - PQRS Pendientes: `linear-gradient(135deg, #F7E3DC 0%, #FBF0EC 100%)`, accent `#E05A47`
   - Use deep forest ink `#102A21` for numbers and headings so readability remains effortless.

4. **Bottom Section 2-Column Layout & Matching Chart (`templates/dashboard.html` & `static/css/dashboard.css`)**:
   - Convert the bottom container into a 2-column grid (`grid-template-columns: 6fr 4fr; gap: 24px;`, `1fr` on mobile/tablet):
     - Left (60%): "Ventas de instalación" bar chart inside a soft mint-tinted card (`rgba(235, 248, 242, 0.75)`), updating bar colors to vibrant water/forest gradients (`#1E88A8`, `#1B7A43`, `#269B63`, `#135E3D`).
     - Right (40%): "Actividad Reciente" panel with the same soft mint-tinted card style, featuring 3–4 realistic water utility updates with glowing status dots (`#1B7A43`, `#E05A47`, `#1E88A8`).

## Validation
- Run the app and verify in the browser that there are zero plain white boxes, the topographic/wave SVG patterns render cleanly, glassmorphic cards show depth over the patterned background, and all text has strong contrast.
