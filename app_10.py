import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import polyline
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import time
import random
import geocoder
# [CHỈNH SỬA 1]: Thêm timedelta để xử lý múi giờ Việt Nam
from datetime import datetime, timedelta  
from streamlit_geolocation import streamlit_geolocation 

# Khởi tạo Session State để lưu tọa độ khi click trên bản đồ
if 'pickup_coord' not in st.session_state:
    st.session_state.pickup_coord = None
if 'dropoff_coord' not in st.session_state:
    st.session_state.dropoff_coord = None
if 'map_mode' not in st.session_state:
    st.session_state.map_mode = "Điểm đón"
if 'gps_auto_assigned' not in st.session_state:
    st.session_state.gps_auto_assigned = False

# ==========================================
# MODULE 1 & 2: LOGIC XỬ LÝ
# ==========================================
def calculate_price_multiplier(weather_val, demand_val, distance_val, time_val):
    weather = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'weather')       
    demand = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'demand')         
    distance = ctrl.Antecedent(np.arange(0, 50.1, 0.1), 'distance')       
    time_var = ctrl.Antecedent(np.arange(0, 24.1, 0.1), 'time') 

    multiplier = ctrl.Consequent(np.arange(0.8, 2.1, 0.1), 'multiplier')

    weather['clear'] = fuzz.trimf(weather.universe, [0, 0, 4.0])       
    weather['light_rain'] = fuzz.trimf(weather.universe, [3.0, 5.5, 8.0]) 
    weather['heavy_rain'] = fuzz.trimf(weather.universe, [7.0, 10, 10])   

    demand['low'] = fuzz.trimf(demand.universe, [0, 0, 4.5])
    demand['medium'] = fuzz.trimf(demand.universe, [3.5, 6.0, 8.5])
    demand['high'] = fuzz.trimf(demand.universe, [7.5, 10, 10])

    distance['short'] = fuzz.trimf(distance.universe, [0, 0, 10.0])       
    distance['medium'] = fuzz.trimf(distance.universe, [5.0, 15.0, 25.0]) 
    distance['long'] = fuzz.trimf(distance.universe, [20.0, 50.0, 50.0])  

    time_var['bandem'] = fuzz.trimf(time_var.universe, [0, 2, 6])          
    time_var['binhthuong'] = fuzz.trimf(time_var.universe, [5, 11, 16])    
    time_var['caodiem'] = fuzz.trimf(time_var.universe, [15, 18, 22])
    
    multiplier['low'] = fuzz.trimf(multiplier.universe, [0.8, 0.8, 1.2])
    multiplier['normal'] = fuzz.trimf(multiplier.universe, [1.0, 1.2, 1.5])
    multiplier['high'] = fuzz.trimf(multiplier.universe, [1.3, 1.7, 2.0])

    rule1 = ctrl.Rule(weather['clear'] & demand['low'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule2 = ctrl.Rule(weather['clear'] & demand['low'] & distance['short'] & time_var['bandem'], multiplier['low'])
    rule3 = ctrl.Rule(weather['clear'] & demand['low'] & distance['short'] & time_var['caodiem'], multiplier['low'])
    rule4 = ctrl.Rule(weather['clear'] & demand['low'] & distance['medium'] & time_var['binhthuong'], multiplier['low'])
    rule5 = ctrl.Rule(weather['clear'] & demand['low'] & distance['medium'] & time_var['bandem'], multiplier['low'])
    rule6 = ctrl.Rule(weather['clear'] & demand['low'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule7 = ctrl.Rule(weather['clear'] & demand['low'] & distance['long'] & time_var['binhthuong'], multiplier['low'])
    rule8 = ctrl.Rule(weather['clear'] & demand['low'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule9 = ctrl.Rule(weather['clear'] & demand['low'] & distance['long'] & time_var['caodiem'], multiplier['normal'])

    rule10 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule11 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['short'] & time_var['bandem'], multiplier['low'])
    rule12 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule13 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['medium'] & time_var['binhthuong'], multiplier['low'])
    rule14 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule15 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule16 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule17 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule18 = ctrl.Rule(weather['clear'] & demand['medium'] & distance['long'] & time_var['caodiem'], multiplier['normal'])

    rule19 = ctrl.Rule(weather['clear'] & demand['high'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule20 = ctrl.Rule(weather['clear'] & demand['high'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule21 = ctrl.Rule(weather['clear'] & demand['high'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule22 = ctrl.Rule(weather['clear'] & demand['high'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule23 = ctrl.Rule(weather['clear'] & demand['high'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule24 = ctrl.Rule(weather['clear'] & demand['high'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule25 = ctrl.Rule(weather['clear'] & demand['high'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule26 = ctrl.Rule(weather['clear'] & demand['high'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule27 = ctrl.Rule(weather['clear'] & demand['high'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    rule28 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule29 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['short'] & time_var['bandem'], multiplier['low'])
    rule30 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule31 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['medium'] & time_var['binhthuong'], multiplier['low'])
    rule32 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule33 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule34 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule35 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule36 = ctrl.Rule(weather['light_rain'] & demand['low'] & distance['long'] & time_var['caodiem'], multiplier['normal'])

    rule37 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule38 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule39 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule40 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule41 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule42 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule43 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule44 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule45 = ctrl.Rule(weather['light_rain'] & demand['medium'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    rule46 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['short'] & time_var['binhthuong'], multiplier['normal'])
    rule47 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule48 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule49 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule50 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule51 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['medium'] & time_var['caodiem'], multiplier['high'])
    rule52 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule53 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['long'] & time_var['bandem'], multiplier['high'])
    rule54 = ctrl.Rule(weather['light_rain'] & demand['high'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    rule55 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['short'] & time_var['binhthuong'], multiplier['low'])
    rule56 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule57 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule58 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule59 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule60 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['medium'] & time_var['caodiem'], multiplier['normal'])
    rule61 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule62 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['long'] & time_var['bandem'], multiplier['normal'])
    rule63 = ctrl.Rule(weather['heavy_rain'] & demand['low'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    rule64 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['short'] & time_var['binhthuong'], multiplier['normal'])
    rule65 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule66 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['short'] & time_var['caodiem'], multiplier['normal'])
    rule67 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule68 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['medium'] & time_var['bandem'], multiplier['normal'])
    rule69 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['medium'] & time_var['caodiem'], multiplier['high'])
    rule70 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['long'] & time_var['binhthuong'], multiplier['normal'])
    rule71 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['long'] & time_var['bandem'], multiplier['high'])
    rule72 = ctrl.Rule(weather['heavy_rain'] & demand['medium'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    rule73 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['short'] & time_var['binhthuong'], multiplier['normal'])
    rule74 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['short'] & time_var['bandem'], multiplier['normal'])
    rule75 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['short'] & time_var['caodiem'], multiplier['high'])
    rule76 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['medium'] & time_var['binhthuong'], multiplier['normal'])
    rule77 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['medium'] & time_var['bandem'], multiplier['high'])
    rule78 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['medium'] & time_var['caodiem'], multiplier['high'])
    rule79 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['long'] & time_var['binhthuong'], multiplier['high'])
    rule80 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['long'] & time_var['bandem'], multiplier['high'])
    rule81 = ctrl.Rule(weather['heavy_rain'] & demand['high'] & distance['long'] & time_var['caodiem'], multiplier['high'])

    all_rules = [locals()[f'rule{i}'] for i in range(1, 82)]

    pricing_ctrl = ctrl.ControlSystem(all_rules)
    pricing_sim = ctrl.ControlSystemSimulation(pricing_ctrl)

    pricing_sim.input['weather'] = weather_val
    pricing_sim.input['demand'] = demand_val
    pricing_sim.input['distance'] = distance_val
    pricing_sim.input['time'] = time_val

    try:
        pricing_sim.compute()
        return pricing_sim.output['multiplier']
    except Exception as e:
        return 1.0 

def get_coordinates(address, ten_diem="Địa chỉ"):
    if address.strip().lower() in ["vị trí của bạn", ""]:
        # Trả về tọa độ GPS thực tế nếu đã lấy được, nếu chưa thì dùng mặc định
        if 'user_gps' in st.session_state and st.session_state.user_gps is not None:
            return st.session_state.user_gps
        return (10.7769, 106.7009) # Mặc định dự phòng
    
    search_text = address + ", Ho Chi Minh City, Vietnam"
    
    try:
        g = geocoder.arcgis(search_text)
        if g.ok: return (g.lat, g.lng)
    except: pass
        
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': search_text, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'SmartDispatchApp_Test/1.0'}
        response = requests.get(url, params=params, headers=headers).json()
        if len(response) > 0:
            return (float(response[0]['lat']), float(response[0]['lon']))
    except: pass

    st.error(f"❌ Không thể tìm thấy tọa độ cho **{ten_diem}**: '{address}'. Vui lòng thử đổi tên khác hoặc click thẳng trên bản đồ.")
    return None

def get_route_osrm(point_a, point_b):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{point_a[1]},{point_a[0]};{point_b[1]},{point_b[0]}?overview=full"
        response = requests.get(url).json()
        if response.get("code") == "Ok":
            route = response["routes"][0]
            return route["distance"] / 1000, route["duration"] / 60, polyline.decode(route["geometry"]) 
    except: pass
    return None, None, None

def get_realtime_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url).json()
        weather_code = response['current_weather']['weathercode']
        
        if weather_code in [0, 1, 2, 3]: 
            return round(random.uniform(0.5, 2.5), 1) 
        elif weather_code in [45, 48, 51, 53, 55, 61]: 
            return round(random.uniform(4.0, 6.0), 1)
        else: 
            return round(random.uniform(7.5, 9.5), 1)
    except:
        return 2.0 

def get_realtime_demand(dist_km, time_min):
    if time_min == 0: return 5.0
    
    speed_kmh = dist_km / (time_min / 60)
    
    if speed_kmh >= 40: 
        return round(random.uniform(1.0, 3.5), 1) 
    elif speed_kmh >= 25: 
        return round(random.uniform(4.0, 6.5), 1)
    elif speed_kmh >= 15: 
        return round(random.uniform(7.0, 8.5), 1)
    else: 
        return round(random.uniform(9.0, 10.0), 1)

# ==========================================
# MODULE 3: GIAO DIỆN APP ĐƯỢC REDESIGN
# ==========================================
st.set_page_config(page_title="Smart Dispatch App", page_icon="🚖", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button { border-radius: 8px; height: 50px; font-weight: bold; font-size: 16px; }
    div[data-testid="metric-container"] {
        background-color: #f7f9fc; border: 1px solid #e0e6ed; padding: 5% 10% 5% 10%;
        border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🚖 Smart Dispatch System</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6B7280; margin-bottom: 30px;'>Nền tảng điều phối xe thông minh tích hợp AI Routing & Fuzzy Logic</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2.5], gap="large")

with col1:
    st.markdown("### 📍 Thông tin chuyến đi")
    with st.container(border=True):
        
        st.markdown("**1. Lấy vị trí GPS thực tế của bạn:**")
        gps_location = streamlit_geolocation()
        if gps_location and gps_location.get('latitude') is not None:
            st.session_state.user_gps = (gps_location['latitude'], gps_location['longitude'])
            
            if not st.session_state.gps_auto_assigned:
                st.session_state.pickup_coord = st.session_state.user_gps
                st.session_state.gps_auto_assigned = True
            
            st.success("✅ Đã lấy được tọa độ GPS!")

            if st.session_state.pickup_coord != st.session_state.user_gps:
                if st.button("📍 Dùng lại vị trí GPS này làm Điểm Đón"):
                    st.session_state.pickup_coord = st.session_state.user_gps
                    st.rerun()

        st.markdown("**2. Chọn bằng cách click trên bản đồ:**")
        st.session_state.map_mode = st.radio("Đang chọn tọa độ cho:", ["Điểm đón", "Điểm đến"], horizontal=True)
        if st.button("🔄 Xóa điểm đã chọn trên bản đồ"):
            st.session_state.pickup_coord = None
            st.session_state.dropoff_coord = None
            st.rerun()

        st.markdown("**3. Hoặc tìm bằng văn bản:**") 
        pickup_address = st.text_input("🟢 Điểm đón", value="Vị trí của bạn", disabled=(st.session_state.pickup_coord is not None))
        if st.session_state.pickup_coord:
            st.success(f"Đã ghim Điểm Đón: {st.session_state.pickup_coord[0]:.4f}, {st.session_state.pickup_coord[1]:.4f}")

        dropoff_address = st.text_input("🔴 Điểm đến", placeholder="Ví dụ: Landmark 81...", disabled=(st.session_state.dropoff_coord is not None))
        if st.session_state.dropoff_coord:
            st.success(f"Đã ghim Điểm Đến: {st.session_state.dropoff_coord[0]:.4f}, {st.session_state.dropoff_coord[1]:.4f}")

        car_type = st.selectbox("🚗 Loại xe", ["Xe 4 Chỗ (Tiết kiệm)", "Xe 7 Chỗ (Rộng rãi)"])
        st.markdown("<br>", unsafe_allow_html=True)
        book_button = st.button("🚀 TÌM XE NGAY", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("📡 **System Status**: Đa luồng (Text & Map Click) | 🟢 GPS: Sẵn sàng")

with col2:
    # [CHỈNH SỬA 2]: Lấy thời gian UTC cộng thêm 7 tiếng (Giờ Việt Nam)
    now = datetime.utcnow() + timedelta(hours=7)
    current_time_val = now.hour + (now.minute / 60.0)

    center_lat, center_lon = 10.7769, 106.7009
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="http://mt0.google.com/vt/lyrs=m&hl=vi&x={x}&y={y}&z={z}",attr="Google Maps") 
    m.add_child(folium.LatLngPopup()) 

    if st.session_state.pickup_coord:
        folium.Marker(st.session_state.pickup_coord, popup="Điểm đón", icon=folium.Icon(color="green", icon="info-sign")).add_to(m)
    if st.session_state.dropoff_coord:
        folium.Marker(st.session_state.dropoff_coord, popup="Điểm đến", icon=folium.Icon(color="red", icon="flag")).add_to(m)

    route_metrics_html = None 

    if book_button:
        if dropoff_address == "" and st.session_state.dropoff_coord is None:
            st.warning("⚠️ Vui lòng nhập điểm đến hoặc chọn trên bản đồ!")
        else:
            with st.spinner('🔄 Hệ thống đang tính toán lộ trình và thu thập dữ liệu thời tiết thực tế...'):
                coord_A = st.session_state.pickup_coord if st.session_state.pickup_coord else get_coordinates(pickup_address, "Điểm Đón")
                coord_B = st.session_state.dropoff_coord if st.session_state.dropoff_coord else get_coordinates(dropoff_address, "Điểm Đến")
                
                if coord_A and coord_B:
                    dist_km, time_min, route_coords = get_route_osrm(coord_A, coord_B)
                    
                    if dist_km is not None:
                        auto_weather = get_realtime_weather(coord_A[0], coord_A[1])
                        auto_demand = get_realtime_demand(dist_km, time_min)
                        
                        multiplier = calculate_price_multiplier(auto_weather, auto_demand, dist_km, current_time_val)
                        
                        base_fare = 15000 if "4" in car_type else 20000
                        price_per_km = 12000 if "4" in car_type else 16000
                        final_price = base_fare + (dist_km * price_per_km * multiplier)
                        
                        folium.PolyLine(route_coords, color="#1E3A8A", weight=5, opacity=0.8).add_to(m)
                        
                        # [CHỈNH SỬA 3]: Bổ sung vẽ marker nếu người dùng lấy tọa độ bằng cách gõ chữ
                        if st.session_state.pickup_coord is None:
                            folium.Marker(coord_A, popup="Điểm đón", icon=folium.Icon(color="green", icon="info-sign")).add_to(m)
                        if st.session_state.dropoff_coord is None:
                            folium.Marker(coord_B, popup="Điểm đến", icon=folium.Icon(color="red", icon="flag")).add_to(m)

                        m.location = [(coord_A[0] + coord_B[0]) / 2, (coord_A[1] + coord_B[1]) / 2]
                        
                        route_success = True
                    else:
                        st.error("❌ Máy chủ OSRM không thể vẽ đường. Vui lòng thử vị trí khác sát đường giao thông hơn!")
                        route_success = False

    map_data = st_folium(m, width=800, height=350, returned_objects=["last_clicked"], key="main_map")

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lng = map_data["last_clicked"]["lng"]
        clicked_coord = (lat, lng)

        if st.session_state.map_mode == "Điểm đón":
            if st.session_state.pickup_coord != clicked_coord:
                st.session_state.pickup_coord = clicked_coord
                st.rerun()
        else:
            if st.session_state.dropoff_coord != clicked_coord:
                st.session_state.dropoff_coord = clicked_coord
                st.rerun()

    if book_button and 'route_success' in locals() and route_success:
        st.success(f"✅ Đã tìm thấy tài xế! Tài xế cách bạn khoảng **{random.randint(3, 5)} phút** di chuyển.") 
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("🛣️ Lộ trình", f"{dist_km:.2f} km")
        m_col2.metric("⏱️ Thời gian dự kiến", f"{time_min:.0f} phút")
        m_col3.metric("💵 Cước phí", f"{final_price:,.0f} đ", f"Hệ số x{multiplier:.2f}", delta_color="inverse")
        
        with st.expander("🤖 Trích xuất dữ liệu điều chỉnh giá (Fuzzy Logic)"):
            st.markdown(f"""
            Hệ thống tự động áp dụng giá linh hoạt dựa trên dữ liệu thời gian thực:
            * **Thời tiết khu vực (Lấy từ Open-Meteo API):** `{auto_weather}/10` 
            * **Mật độ yêu cầu (Tính toán từ tốc độ lưu thông OSRM):** `{auto_demand}/10`
            * **Thời gian gọi xe:** `{now.strftime('%H:%M')} ({current_time_val:.2f}h)`
            """)
        
        st.markdown("#### 🚗 Trạng thái di chuyển")
        my_bar = st.progress(0, text="Tài xế đang đến điểm đón...")
        for percent_complete in range(100):
            time.sleep(0.01) 
            my_bar.progress(percent_complete + 1, text=f"Đang di chuyển: Khớp lộ trình {percent_complete + 1}%")
        st.info("🎉 Hành trình hoàn tất. Cảm ơn bạn đã sử dụng dịch vụ!")
