import streamlit as st
import pandas as pd
import json
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Adrián", page_icon="💰", layout="wide")

# --- 2. CONTROL DE ACCESO ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "ttoty13" and st.session_state["password"] == "922292":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    return st.session_state["password_correct"]

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Sistema Financiero", layout="wide", page_icon="💰")

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem; }
    .date-red { color: #ff4b4b; font-weight: bold; }
    .pb-header-expense { color: #ff4b4b; font-size: 1.2rem; font-weight: bold; } 
    .pb-header-saving { color: #2ecc71; font-size: 1.2rem; font-weight: bold; } 
    button[data-baseweb="tab"] div p { font-size: 1.1rem !important; font-weight: 500 !important; }
    .stAlert { padding: 0.5rem 1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNCIONES BASE ---

def parse_date(date_obj):
    if not date_obj: return datetime.now()
    if isinstance(date_obj, dict) and 'seconds' in date_obj:
        return datetime.fromtimestamp(date_obj['seconds'])
    elif isinstance(date_obj, str):
        clean_date = date_obj.replace('Z', '')
        try: return datetime.fromisoformat(clean_date)
        except: pass
        try: return datetime.strptime(clean_date, "%Y-%m-%d")
        except: pass
        try: return datetime.strptime(clean_date, "%d/%m/%Y")
        except: pass
        try: return datetime.strptime(clean_date, "%d/%m/%Y %H:%M")
        except: pass
    elif isinstance(date_obj, datetime):
        return date_obj
    return datetime.now()

def to_firebase_date(py_date):
    ts = datetime(py_date.year, py_date.month, py_date.day).timestamp()
    return {"seconds": int(ts), "nanoseconds": 0}

def get_safe_total(h):
    q = float(h.get('quantity', 0))
    p = float(h.get('price', 0))
    tv = float(h.get('totalValue', 0))
    return tv if tv > 0 else q * p

def convert_currency(amount, src_curr, dest_curr, rate):
    if src_curr == dest_curr: return amount
    if src_curr == 'USD' and dest_curr == 'ARS': return amount * rate
    if src_curr == 'ARS' and dest_curr == 'USD': return amount / rate if rate > 0 else 0
    return amount

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.header("💱 Cotizaciones")
    
    # --- SECCIÓN DÓLAR ---
    tipo_dolar = st.selectbox("Tipo Dólar", ["Blue", "Oficial", "MEP", "Manual"])
    
    @st.cache_data(ttl=3600)
    def obtener_cotizacion_api(tipo="blue"):
        try:
            url = f"https://dolarapi.com/v1/dolares/{tipo}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return float(resp.json().get('venta', 0))
        except: return None
        return None

    val_api = obtener_cotizacion_api(tipo_dolar.lower())
    cotizacion_actual = st.number_input("Dólar Hoy ($)", value=float(val_api if val_api else 1435.0))
    
    # --- SECCIÓN UVA ---
    @st.cache_data(ttl=3600)
    def obtener_uva_api():
        try:
            url = "https://dolarapi.com/v1/cotizaciones/uva"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return float(data.get('venta', data.get('valor', 0)))
        except: return None
        return None
        
    val_uva_api = obtener_uva_api()
    uva_actual = st.number_input("Valor UVA Hoy ($)", value=float(val_uva_api if val_uva_api else 900.0), format="%.2f")

    st.markdown("---")
    st.header("🧮 Sumadora")
    
    def procesar_suma_callback():
        try:
            if 'sumadora_total' not in st.session_state: st.session_state.sumadora_total = 0.0
            st.session_state.sumadora_total += float(st.session_state.temp_monto_txt.replace(',', '.'))
        except: pass
        st.session_state.temp_monto_txt = ""

    if 'sumadora_total' not in st.session_state: st.session_state.sumadora_total = 0.0
    st.text_input("Monto + Enter", key="temp_monto_txt", on_change=procesar_suma_callback)
    if st.button("🔄 Limpiar Suma"): st.session_state.sumadora_total = 0.0; st.rerun()
    st.subheader(f"Total: $ {st.session_state.sumadora_total:,.2f}")

    # SELECTOR DE ARCHIVO
    st.markdown("---")
    st.subheader("📂 Archivo de Datos")
    folder_path = '.'
    files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    
    if not files:
        st.error("No hay JSONs.")
        FILE_NAME = "sin_datos.json"
    else:
        FILE_NAME = st.selectbox("Backup:", files, index=0)
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(FILE_NAME)).strftime('%d/%m/%Y %H:%M')
            st.caption(f"📅: {mod_time}")
        except: pass

# --- CARGA DE DATOS ---
def load_data():
    if not os.path.exists(FILE_NAME): return {}
    try:
        with open(FILE_NAME, 'r', encoding='utf-8') as f:
            data = json.load(f)
            root = data.get('data', {})
            
            if 'piggyBanks' not in root: root['piggyBanks'] = []
            if 'piggyBankExpenses' not in root: root['piggyBankExpenses'] = []
            if 'loan_payments' not in root: root['loan_payments'] = [] 
            
            # AUTO-CREACIÓN DEL PIGGYBANK "PRÉSTAMO (CAPITAL)"
            existe_prestamo = False
            for pb in root['piggyBanks']:
                if pb.get('name') == "Préstamo (Capital)":
                    existe_prestamo = True
                    if not pb.get('id'): pb['id'] = "pb_prestamo_capital" 
                    break
            
            if not existe_prestamo:
                root['piggyBanks'].append({
                    "id": "pb_prestamo_capital",
                    "name": "Préstamo (Capital)",
                    "type": "GASTO",
                    "currency": "ARS",
                    "order": 0
                })

            for pb in root['piggyBanks']:
                if 'type' not in pb: pb['type'] = 'GASTO'
                if 'currency' not in pb: pb['currency'] = 'ARS'
            return data
    except: return {}

def save_data(data):
    try:
        with open(FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        st.toast("✅ Cambios guardados")
    except Exception as e:
        st.error(f"Error al guardar: {e}")

if 'data' not in st.session_state:
    st.session_state.data = load_data()
    st.session_state.current_file = FILE_NAME
elif st.session_state.get('current_file') != FILE_NAME:
    st.session_state.data = load_data()
    st.session_state.current_file = FILE_NAME

root_data = st.session_state.data.get('data', {})
snapshots = root_data.get('snapshots', [])
investments = root_data.get('investments', [])
categories = root_data.get('categories', [])
expenses = root_data.get('piggyBankExpenses', [])
piggy_banks = root_data.get('piggyBanks', [])
loan_payments = root_data.get('loan_payments', [])

# --- 4. INTERFAZ PRINCIPAL ---
tab1, tab2, tab3, tab5, tab4 = st.tabs(["📊 Evolución", "📈 Inversiones", "💸 Gastos", "🏦 Préstamo", "⚙️ Configuración"])

# --- PESTAÑA 1: EVOLUCIÓN ---
with tab1:
    history_map = {}
    evo_total_data = []

    if snapshots:
        snapshots.sort(key=lambda x: parse_date(x['date']).timestamp())
        for s in snapshots:
            d_s = parse_date(s['date'])
            rate_s = float(s.get('exchangeRate', cotizacion_actual))
            
            ars_s, usd_s = 0, 0
            for e in s.get('entries', []):
                name = e.get('name', e.get('categoryName'))
                curr = e.get('currency', 'ARS')
                val = float(e.get('value', 0))
                
                k = f"{name} ({curr})"
                if k not in history_map: history_map[k] = []
                history_map[k].append({'fecha': d_s, 'valor': val, 'snap_id': s.get('id')})
                
                if curr == 'USD': usd_s += val
                else: ars_s += val
            
            evo_total_data.append({'f': d_s, 'v': usd_s + (ars_s / rate_s if rate_s > 0 else 0)})

    total_patrimonio_usd_calculado = 0
    for cat in categories:
        k_cat = f"{cat['name']} ({cat['currency']})"
        saldo_actual = 0
        if k_cat in history_map:
            saldo_actual = history_map[k_cat][-1]['valor']
        val_en_usd = convert_currency(saldo_actual, cat['currency'], 'USD', cotizacion_actual)
        total_patrimonio_usd_calculado += val_en_usd

    total_patrimonio_ars_calculado = total_patrimonio_usd_calculado * cotizacion_actual

    col_k, col_g = st.columns([2, 1.5])
    with col_k:
        ck1, ck2 = st.columns(2)
        ck1.metric("Patrimonio Total (USD)", f"u$s {total_patrimonio_usd_calculado:,.2f}")
        ck2.metric("Patrimonio Total (ARS)", f"$ {total_patrimonio_ars_calculado:,.0f}")
    with col_g:
        if evo_total_data: st.line_chart(pd.DataFrame(evo_total_data).set_index('f'), height=80)

    st.divider()
    st.write("### 📅 Detalle de Cuentas")
    
    raw_inv_ars = 0
    raw_inv_usd = 0
    for i in investments:
        h = i.get('valueHistory', [])
        val = get_safe_total(h[-1]) if h else 0
        if i.get('currency') == 'ARS': raw_inv_ars += val
        elif i.get('currency') == 'USD': raw_inv_usd += val
    
    for cat in sorted(categories, key=lambda x: x.get('order', 99)):
        k = f"{cat['name']} ({cat['currency']})"
        l_v = 0; l_d = None
        if k in history_map:
            h = history_map[k]
            l_v = h[-1]['valor']
            l_d = h[-1]['fecha']

        d_cls = "date-red" if l_d and (datetime.now() - l_d).days > 30 else ""
        date_str = l_d.strftime('%d/%m/%Y') if l_d else "Sin datos"
        val_usd_show = convert_currency(l_v, cat['currency'], 'USD', cotizacion_actual)
        
        st.markdown(f"**📂 {cat['name']}** — {cat['currency']} {l_v:,.2f} (**u$s {val_usd_show:,.2f}**) | <span class='{d_cls}'>Carga: {date_str}</span>", unsafe_allow_html=True)
        
        with st.expander("Gestionar cuenta"):
            c_in, c_gr = st.columns([1, 2])
            with c_in:
                f_ev = st.date_input("Fecha carga", value=datetime.now(), key=f"d_ev_{k}")
                v_sug = l_v
                if "inversiones" in cat['name'].lower():
                    if cat['currency'] == 'ARS': v_sug = raw_inv_ars
                    elif cat['currency'] == 'USD': v_sug = raw_inv_usd
                v_ev = st.number_input(f"Saldo {cat['name']}", value=float(v_sug), format="%.2f", key=f"v_ev_{k}")
                
                if st.button("💾 Guardar Balance", key=f"b_ev_{k}"):
                    td = datetime(f_ev.year, f_ev.month, f_ev.day).date()
                    ex = next((s for s in snapshots if parse_date(s['date']).date() == td), None)
                    ne = {"name": cat['name'], "value": v_ev, "currency": cat['currency'], "categoryId": cat.get('id','')}
                    if ex:
                        ents = ex.get('entries', [])
                        found = False
                        for i, e in enumerate(ents):
                            if e.get('name') == cat['name'] and e.get('currency') == cat['currency']:
                                ents[i]['value'] = v_ev; found = True; break
                        if not found: ents.append(ne)
                    else:
                        ns = {"id": f"s_{int(datetime.now().timestamp())}", "date": to_firebase_date(f_ev), "exchangeRate": cotizacion_actual, "entries": [ne]}
                        root_data['snapshots'].append(ns)
                    save_data(st.session_state.data); st.rerun()
            with c_gr:
                if k in history_map: st.line_chart(pd.DataFrame(history_map[k]).set_index('fecha')['valor'], height=150)
            with st.expander("📜 Ver/Editar Historial"):
                if k in history_map:
                    df_h = pd.DataFrame(history_map[k])
                    st.data_editor(df_h, column_config={"snap_id": None, "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")}, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_ev_hist_{k}")

# --- PESTAÑA 2: INVERSIONES ---
with tab2:
    total_global_usd = 0
    total_global_ars = 0
    chart_data = [] 
    for i in investments:
        h = i.get('valueHistory', [])
        val_orig = get_safe_total(h[-1]) if h else 0
        curr = i.get('currency', 'ARS')
        if curr == 'USD':
            val_usd = val_orig
            val_ars = convert_currency(val_orig, 'USD', 'ARS', cotizacion_actual)
        else:
            val_ars = val_orig
            val_usd = convert_currency(val_orig, 'ARS', 'USD', cotizacion_actual)
        total_global_usd += val_usd
        total_global_ars += val_ars
        if val_usd > 0: chart_data.append({"Activo": i.get('name'), "ValorUSD": val_usd})

    col_k, col_p = st.columns([2, 1])
    with col_k:
        ck1, ck2 = st.columns(2)
        ck1.metric("Total Invertido (USD)", f"u$s {total_global_usd:,.2f}")
        ck2.metric("Total Invertido (ARS)", f"$ {total_global_ars:,.0f}")
    with col_p:
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.pie(df_chart, values='ValorUSD', names='Activo', hole=0.5, height=160)
            fig.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    chk_ocultar_cero = st.checkbox("✅ Ocultar inversiones en cero", value=True)
    
    for inv in sorted(investments, key=lambda x: x.get('order', 99)):
        h = inv.get('valueHistory', [])
        if h:
            last = h[-1]
            v_c = get_safe_total(last)
            q_c = float(last.get('quantity', 0))
            p_c = float(last.get('price', 0))
            l_d = parse_date(last.get('date'))
        else:
            v_c = 0; q_c = 0; p_c = 0; l_d = None
        if chk_ocultar_cero and v_c == 0: continue

        d_cls = "date-red" if l_d and (datetime.now() - l_d).days > 30 else ""
        date_str = l_d.strftime('%d/%m/%Y') if l_d else "-"
        val_usd_header = convert_currency(v_c, inv['currency'], 'USD', cotizacion_actual)
        st.markdown(f"**💹 {inv['name']}** — {q_c:,.4f} títulos | **{inv['currency']} {v_c:,.2f}** (u$s {val_usd_header:,.2f}) | <span class='{d_cls}'>Uf: {date_str}</span>", unsafe_allow_html=True)
        
        with st.expander(f"Gestionar {inv['name']}"):
            ca, cb = st.columns([1, 2])
            with ca:
                f_in = st.date_input("Fecha", value=datetime.now(), key=f"fi_{inv['name']}")
                q_in = st.number_input("Cantidad Títulos", value=float(q_c), format="%.4f", key=f"qi_{inv['name']}")
                t_in = st.number_input(f"Monto TOTAL ({inv['currency']})", value=float(v_c), format="%.2f", key=f"ti_{inv['name']}")
                if st.button("💾 Guardar Carga", key=f"btn_i_{inv['name']}"):
                    pc = t_in / q_in if q_in > 0 else 0
                    new_h = {"date": to_firebase_date(f_in), "quantity": q_in, "price": pc, "totalValue": t_in, "exchangeRate": cotizacion_actual}
                    if 'valueHistory' not in inv: inv['valueHistory'] = []
                    inv['valueHistory'].append(new_h)
                    save_data(st.session_state.data); st.rerun()
            with cb:
                if h: st.line_chart(pd.DataFrame([{"f": parse_date(x['date']), "v": get_safe_total(x)} for x in h]).set_index('f')['v'], height=180)
            with st.expander("📜 Ver/Editar Historial"):
                if h:
                    raw_h = [{"fecha": parse_date(x['date']), "cantidad": x.get('quantity',0), "precio": x.get('price',0), "total": get_safe_total(x)} for x in h]
                    ed_inv = st.data_editor(pd.DataFrame(raw_h), column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")}, num_rows="dynamic", use_container_width=True, key=f"ed_inv_{inv['name']}")
                    if st.button("Aplicar Corrección", key=f"fix_{inv['name']}"):
                        new_h_list = [{"date": to_firebase_date(r['fecha']), "quantity": r['cantidad'], "price": r['precio'], "totalValue": r['total']} for r in ed_inv.to_dict('records')]
                        inv['valueHistory'] = new_h_list; save_data(st.session_state.data); st.rerun()

# --- PESTAÑA 3: GASTOS ---
with tab3:
    st.header("💸 Detalle de Gastos")
    pb_list = sorted(piggy_banks, key=lambda x: x.get('order', 99))
    if expenses:
        df_all_exp = pd.DataFrame([{"fecha": parse_date(e['date']), "bid": e.get('piggyBankId', e.get('bankId')), "monto": float(e.get('amount', 0)), "moneda": e.get('currency', 'ARS'), "desc": e.get('description', ''), "raw": e} for e in expenses])
    else:
        df_all_exp = pd.DataFrame(columns=["fecha", "bid", "monto", "moneda", "desc"])

    for pb in pb_list:
        pb_id = pb.get('id'); pb_name = pb.get('name', 'N/A'); pb_curr = pb.get('currency', 'ARS')
        pb_type = pb.get('type', 'GASTO').upper()
        css_class = "pb-header-expense" if "GASTO" in pb_type else "pb-header-saving"
        df_c = df_all_exp[df_all_exp['bid'] == pb_id].sort_values('fecha').copy()
        total_orig = 0; total_usd_equiv = 0
        if not df_c.empty:
            df_c['monto_norm'] = df_c.apply(lambda r: convert_currency(r['monto'], r.get('moneda', pb_curr), pb_curr, cotizacion_actual), axis=1)
            total_orig = df_c['monto_norm'].sum()
            total_usd_equiv = convert_currency(total_orig, pb_curr, 'USD', cotizacion_actual)
            
        st.markdown(f"<div class='{css_class}'>📂 {pb_name} — Total: {pb_curr} {total_orig:,.2f} (u$s {total_usd_equiv:,.2f})</div>", unsafe_allow_html=True)
        with st.expander(f"Movimientos de {pb_name}"):
            c1, c2 = st.columns([1, 2])
            with c1:
                f_g = st.date_input("Fecha", value=datetime.now(), key=f"fg_{pb_id}")
                cx1, cx2 = st.columns([1, 2])
                curr_g = cx1.selectbox("Moneda", ["ARS", "USD"], index=0 if pb_curr == "ARS" else 1, key=f"curr_{pb_id}")
                m_g = cx2.number_input(f"Monto", value=0.0, key=f"mg_{pb_id}")
                d_g = st.text_input("Nota", key=f"dg_{pb_id}")
                if st.button("💾 Registrar", key=f"bg_{pb_id}", use_container_width=True):
                    ng = {"date": to_firebase_date(f_g), "amount": m_g, "currency": curr_g, "piggyBankId": pb_id, "description": d_g}
                    root_data['piggyBankExpenses'].append(ng)
                    save_data(st.session_state.data); st.rerun()
            with c2:
                if not df_c.empty: st.line_chart(df_c.set_index('fecha')['monto_norm'], height=150)
            with st.expander("📜 Ver/Editar Historial"):
                if not df_c.empty:
                    ed_g = st.data_editor(df_c[['fecha', 'moneda', 'monto', 'desc']], column_config={"fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"), "moneda": st.column_config.SelectboxColumn("Moneda", options=["ARS", "USD"], required=True)}, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_g_{pb_id}")
                    if st.button("⚠️ Aplicar", key=f"bfg_{pb_id}"):
                        keep = [e for e in root_data['piggyBankExpenses'] if e.get('piggyBankId') != pb_id and e.get('bankId') != pb_id]
                        for row in ed_g.to_dict('records'):
                            keep.append({"date": to_firebase_date(row['fecha']), "amount": row['monto'], "currency": row['moneda'], "piggyBankId": pb_id, "description": row['desc']})
                        root_data['piggyBankExpenses'] = keep; save_data(st.session_state.data); st.rerun()

# --- PESTAÑA 5: PRÉSTAMO (CON RECORDATORIO) ---
with tab5:
    st.subheader("🏦 Control de Préstamo (UVA)")
    
    # --- BUSCAMOS EL PIGGYBANK DEL CAPITAL ---
    loan_pb_obj = next((pb for pb in root_data['piggyBanks'] if pb.get('name') == "Préstamo (Capital)"), None)
    
    # --- LÓGICA DE RECORDATORIO ---
    fecha_inicio_prestamo = datetime(2026, 3, 11)
    fecha_hoy = datetime.now()
    diff_meses = (fecha_hoy.year - fecha_inicio_prestamo.year) * 12 + (fecha_hoy.month - fecha_inicio_prestamo.month)
    cuota_sugerida_num = diff_meses + 1
    if cuota_sugerida_num < 1: cuota_sugerida_num = 1
    if cuota_sugerida_num > 180: cuota_sugerida_num = 180

    mes_actual = fecha_hoy.month
    anio_actual = fecha_hoy.year
    dia_actual = fecha_hoy.day
    
    pagado_este_mes = False
    for p in loan_payments:
        d_p = parse_date(p['date'])
        if d_p.month == mes_actual and d_p.year == anio_actual:
            pagado_este_mes = True
            break
    
    if pagado_este_mes:
        st.success(f"✅ La cuota de este mes ({fecha_hoy.strftime('%B')}) ya está pagada.")
    else:
        if dia_actual < 11:
            dias_restantes = 11 - dia_actual
            st.warning(f"⚠️ **ATENCIÓN:** La cuota vence en {dias_restantes} días (el día 11).")
        elif dia_actual == 11:
            st.warning("⚠️ **HOY** vence la cuota del préstamo.")
        else:
            st.error(f"🚨 **VENCIDA:** La cuota venció el día 11 de este mes y aún no se registra pago.")

    st.divider()

    # --- CÁLCULOS CAPITAL DISPONIBLE ---
    capital_inicial = 25000000.0
    total_movimientos = 0
    df_capital_movs = pd.DataFrame()
    
    if loan_pb_obj:
        pb_id_target = loan_pb_obj.get('id')
        # Filtramos gastos de ESTE piggybank
        movs = [e for e in expenses if e.get('piggyBankId') == pb_id_target or e.get('bankId') == pb_id_target]
        
        # SUMA DIRECTA: Negativo resta (Gasto), Positivo suma (Ingreso/Rendimiento)
        total_movimientos = sum([float(e.get('amount', 0)) for e in movs])
        
        if movs:
            df_capital_movs = pd.DataFrame([
                {
                    "fecha": parse_date(x['date']),
                    "concepto": x.get('description', ''),
                    "monto": x.get('amount', 0),
                    "tipo": "GASTO" if x.get('amount', 0) < 0 else "RENDIMIENTO"
                } for x in movs
            ])

    saldo_remanente = capital_inicial + total_movimientos
    
    # KPIs
    total_pagado_ars = sum([p.get('amount',0) for p in loan_payments])
    total_uvas_acum = sum([p.get('uvas_amount',0) for p in loan_payments])
    
    c_k1, c_k2, c_k3 = st.columns(3)
    c_k1.metric("Total Pagado (Cuotas)", f"$ {total_pagado_ars:,.2f}", f"{total_uvas_acum:,.2f} UVAs")
    c_k2.metric("Capital Inicial", f"$ {capital_inicial:,.0f}")
    c_k3.metric("Saldo Disponible", f"$ {saldo_remanente:,.2f}", delta=f"{total_movimientos:,.2f} Movs.")
    
    st.divider()
    col_izq, col_der = st.columns(2)

    # --- COLUMNA IZQUIERDA: PAGOS ---
    with col_izq:
        st.write("#### 📤 Registro de Pagos (Cuotas)")
        with st.container(border=True):
            f_pago = st.date_input("Fecha Pago", value=datetime.now(), key="lp_date")
            c_p1, c_p2 = st.columns(2)
            m_pago = c_p1.number_input("Monto Pesos ($)", min_value=0.0, key="lp_mount")
            u_pago = c_p2.number_input("Cantidad UVAs", min_value=0.0, format="%.2f", key="lp_uvas")
            nota_sugerida = f"Cuota {cuota_sugerida_num}/180"
            n_pago = st.text_input("Nota", value=nota_sugerida, key="lp_note")
            
            if st.button("💾 Registrar Pago", use_container_width=True):
                new_pay = {"date": to_firebase_date(f_pago), "amount": m_pago, "uvas_amount": u_pago, "note": n_pago}
                root_data['loan_payments'].append(new_pay)
                save_data(st.session_state.data); st.rerun()
        
        if loan_payments:
            df_pay = pd.DataFrame([{"fecha": parse_date(x['date']), "monto": x['amount'], "uvas": x.get('uvas_amount', 0), "nota": x.get('note','')} for x in loan_payments])
            st.dataframe(df_pay.sort_values('fecha', ascending=False), hide_index=True)
            if st.checkbox("Editar Pagos"):
                ed_pay = st.data_editor(df_pay, num_rows="dynamic", key="ed_loan_pay")
                if st.button("Guardar Cambios Pagos"):
                    new_list = [{"date": to_firebase_date(r['fecha']), "amount": r['monto'], "uvas_amount": r['uvas'], "note": r['nota']} for r in ed_pay.to_dict('records')]
                    root_data['loan_payments'] = new_list; save_data(st.session_state.data); st.rerun()

    # --- COLUMNA DERECHA: GESTIÓN CAPITAL ---
    with col_der:
        st.write("#### 📥 Gestión del Capital (Destino)")
        st.info("Registra gastos o rendimientos. Esto se verá reflejado también en la pestaña de Gastos.")
        
        if not loan_pb_obj:
            st.error("Error: No se encontró la cuenta 'Préstamo (Capital)'. Revisa Configuración.")
        else:
            with st.container(border=True):
                f_cap = st.date_input("Fecha", value=datetime.now(), key="lcap_date")
                tipo_mov = st.radio("Tipo Movimiento", ["GASTO (Resta)", "RENDIMIENTO/INGRESO (Suma)"], horizontal=True)
                desc_cap = st.text_input("Descripción (Ej: Compra Materiales, Interés PF)", key="lcap_desc")
                monto_cap = st.number_input("Monto ($)", min_value=0.0, key="lcap_monto")
                
                if st.button("💾 Registrar Movimiento", use_container_width=True):
                    # LÓGICA CORREGIDA:
                    # GASTO = Negativo
                    # INGRESO = Positivo
                    
                    if "GASTO" in tipo_mov:
                        final_amount = -monto_cap # Guardamos negativo para que reste
                    else:
                        final_amount = monto_cap  # Guardamos positivo para que sume
                    
                    new_exp = {
                        "date": to_firebase_date(f_cap),
                        "amount": final_amount,
                        "currency": "ARS",
                        "piggyBankId": loan_pb_obj.get('id'),
                        "description": desc_cap
                    }
                    root_data['piggyBankExpenses'].append(new_exp)
                    save_data(st.session_state.data); st.rerun()
            
            if not df_capital_movs.empty:
                # Mostramos tabla con colores corregidos
                st.dataframe(
                    df_capital_movs.style.format({"monto": "${:,.2f}"})
                    .map(lambda x: 'color: green' if x > 0 else 'color: red', subset=['monto']), 
                    hide_index=True
                )

# --- PESTAÑA 4: CONFIGURACIÓN ---
with tab4:
    st.subheader("⚙️ Configuración")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Inversiones**")
        ed_i = st.data_editor(pd.DataFrame(investments), column_order=["name", "currency", "order"], num_rows="dynamic", key="cfg_i")
        if st.button("💾 Inv."): root_data['investments'] = ed_i.to_dict('records'); save_data(st.session_state.data); st.rerun()
    with c2:
        st.write("**Balance**")
        ed_c = st.data_editor(pd.DataFrame(categories), column_order=["name", "currency", "order"], num_rows="dynamic", key="cfg_c")
        if st.button("💾 Bal."): root_data['categories'] = ed_c.to_dict('records'); save_data(st.session_state.data); st.rerun()
    with c3:
        st.write("**PiggyBanks**")
        ed_pb = st.data_editor(pd.DataFrame(piggy_banks), column_order=["name", "type", "currency", "id"], column_config={"type": st.column_config.SelectboxColumn("Tipo", options=["GASTO", "AHORRO"]), "currency": st.column_config.SelectboxColumn("Moneda", options=["ARS", "USD"]), "id": st.column_config.TextColumn(disabled=True)}, num_rows="dynamic", key="cfg_pb")
        if st.button("💾 Piggy"): 
            new_pb = ed_pb.to_dict('records')
            for p in new_pb: 
                if not p.get('id'): p['id'] = f"pb_{int(datetime.now().timestamp())}_{p.get('name')}"
            root_data['piggyBanks'] = new_pb; save_data(st.session_state.data); st.rerun()

                
        except Exception as e:
            st.error(f"Falla en el procesamiento de datos: {str(e)}")
