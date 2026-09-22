import streamlit as st
import ee
import folium
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
from google.oauth2 import service_account

st.set_page_config(page_title="Dashboard Kualitas Udara Kalteng", layout="wide")
st.caption("Versi web — Google Earth Engine + Folium + Random Forest")
st.markdown("**Lokasi:** Kalimantan Tengah | **Pemodelan:** Random Forest Machine Learning | **Periode:** Agustus 2026")
st.markdown("---")

try:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/earthengine",
            "https://www.googleapis.com/auth/cloud-platform"
        ]
    )

    ee.Initialize(
        credentials=credentials,
        project="wasfiq"
    )

except Exception as e:
    st.error(f"Earth Engine gagal diinisialisasi: {e}")
    st.stop()
roi = ee.FeatureCollection('projects/wasfiq/assets/Kalteng')
start_date = '2026-08-01'
end_date = '2026-08-28'

col1, col2 = st.columns([7, 3])

with col1:
    st.subheader("🗺️ Peta Interaktif Sebaran PM2.5 & Parameter")
    map_dash = folium.Map(
        location=[-1.5, 113.5],
        zoom_start=6,
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap contributors © CARTO",
        subdomains="abcd",
        max_zoom=20
    )

    def add_ee_layer(self, ee_image_object, vis_params, name, show=True):
        map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Map Data &copy; Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            show=show
        ).add_to(self)
    folium.Map.add_ee_layer = add_ee_layer

    # A. Data Meteorologi
    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterBounds(roi).filterDate(start_date, end_date).mean().clip(roi)
    map_dash.add_ee_layer(era5.select('u_component_of_wind_10m'), {'min': -3.0, 'max': 3.0, 'palette': ['blue', 'white', 'red']}, 'Wind_U', show=False)
    map_dash.add_ee_layer(era5.select('temperature_2m'), {'min': 295, 'max': 305, 'palette': ['blue', 'cyan', 'green', 'yellow', 'red']}, 'Temperature_2m', show=False)

    # B. Data Kualitas Udara
    no2 = ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2").filterBounds(roi).filterDate(start_date, end_date).mean().clip(roi)
    map_dash.add_ee_layer(no2.select('NO2_column_number_density'), {'min': 0, 'max': 0.0002, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}, 'NO2', show=False)

    hcho = ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_HCHO").filterBounds(roi).filterDate(start_date, end_date).mean().clip(roi)
    map_dash.add_ee_layer(hcho.select('tropospheric_HCHO_column_number_density'), {'min': 0, 'max': 0.0005, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}, 'HCHO', show=False)

    ai_raw = ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_AER_AI").filterBounds(roi).filterDate(start_date, end_date).mean().clip(roi)
    vis_ai = {'min': 0.0, 'max': 1.5, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']}
    map_dash.add_ee_layer(ai_raw.select('absorbing_aerosol_index'), vis_ai, 'Aerosol Index', show=False)

    # C. Prediksi PM2.5 Menggunakan Random Forest
    with st.spinner("Memuat Data Latih dan Memproses Random Forest..."):
        # Load Predictors
        ai_col = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_AER_AI').filterBounds(roi).filterDate(start_date, end_date).select('absorbing_aerosol_index').mean()
        predictors = ai_col.addBands(era5).addBands(no2).addBands(hcho)
        predictors_renamed = predictors.select(
            ['absorbing_aerosol_index', 'temperature_2m', 'u_component_of_wind_10m', 'NO2_column_number_density', 'tropospheric_HCHO_column_number_density'],
            ['Aerosol_Index', 'Temperature_2m', 'Wind_U', 'NO2_Density', 'HCHO_Density']
        )

        # Load DataFrame hasil simulasi Colab agar 100% Identik
        df_train = pd.read_csv('training_data_pm25.csv')

        # Konversi DataFrame ke ee.FeatureCollection
        ee_features = []
        for index, row in df_train.iterrows():
            feat = ee.Feature(
                ee.Geometry.Point([row['longitude'], row['latitude']]),
                {
                    'Aerosol_Index': row['Aerosol_Index'],
                    'Temperature_2m': row['Temperature_2m'],
                    'Wind_U': row['Wind_U'],
                    'NO2_Density': row['NO2_Density'],
                    'HCHO_Density': row['HCHO_Density'],
                    'Actual_PM25': row['Actual_PM25']
                }
            )
            ee_features.append(feat)

        fc_training = ee.FeatureCollection(ee_features)

        # Melatih Random Forest
        features = ['Aerosol_Index', 'Temperature_2m', 'Wind_U', 'NO2_Density', 'HCHO_Density']
        classifier = ee.Classifier.smileRandomForest(10).setOutputMode('REGRESSION').train(
            features=fc_training,
            classProperty='Actual_PM25',
            inputProperties=features
        )

        # Klasifikasi ke Peta
        predicted_pm25 = predictors_renamed.classify(classifier).clip(roi)

        # Tambahkan Layer ke Peta
        vis_pm25 = {'min': 0, 'max': 100, 'palette': ['008000', 'FFFF00', 'FFA500', 'FF0000', '800080']}
        map_dash.add_ee_layer(predicted_pm25, vis_pm25, 'Prediksi PM2.5', show=True)

        # Tambahkan Zona Bahaya
        danger_zone = predicted_pm25.gt(40)
        danger_masked = danger_zone.updateMask(danger_zone.eq(1))
        map_dash.add_ee_layer(danger_masked, {'min': 0, 'max': 1, 'palette': ['red']}, 'Zona Bahaya PM2.5 (>40)', show=True)

    # D. Batas Kalteng
    empty_image = ee.Image().byte()
    outline = empty_image.paint(featureCollection=roi, color=1, width=2)
    map_dash.add_ee_layer(outline, {'palette': ['black']}, 'Batas Administrasi Kalteng', show=True)

    map_dash.add_child(folium.LayerControl())

    # Menampilkan Peta dengan HTML Component agar aman dari LocalTunnel
    map_html = map_dash._repr_html_()
    components.html(map_html, height=500)

# ================= LEGENDA KUSTOM DI LUAR PETA =================
    with st.expander("📖 Lihat Legenda Parameter (Warna)", expanded=False):
        st.markdown("""
        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px;">
                <b>Prediksi PM2.5 (µg/m³)</b>
                <div style="background: linear-gradient(to right, #008000, #FFFF00, #FFA500, #FF0000, #800080); height: 12px; border-radius: 5px; margin-top: 5px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;"><span>0 (Aman)</span><span>60+ (Bahaya)</span></div>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <b>Aerosol Index (AI)</b>
                <div style="background: linear-gradient(to right, black, blue, purple, cyan, green, yellow, red); height: 12px; border-radius: 5px; margin-top: 5px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;"><span>0.0</span><span>1.5+</span></div>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <b>Suhu Permukaan (Kelvin)</b>
                <div style="background: linear-gradient(to right, blue, cyan, green, yellow, red); height: 12px; border-radius: 5px; margin-top: 5px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;"><span>295 K</span><span>305 K</span></div>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <b>Kecepatan Angin U (m/s)</b>
                <div style="background: linear-gradient(to right, blue, white, red); height: 12px; border-radius: 5px; margin-top: 5px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;"><span>-3.0</span><span>+3.0</span></div>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <b>NO2 / HCHO Density</b>
                <div style="background: linear-gradient(to right, black, blue, purple, cyan, green, yellow, red); height: 12px; border-radius: 5px; margin-top: 5px;"></div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;"><span>0.0 (Rendah)</span><span>Tinggi</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.subheader("📊 Statistik Area Terdampak")
    st.info("Visualisasi Zonal Statistics berdasarkan paparan populasi di atas ambang batas PM2.5 > 40 µg/m³.")

    try:
        # Nama file sesuaikan dengan yang kamu export di Zonal Statistics (Cell 10)
        df_impact = pd.read_csv('data_dampak_kalteng.csv')
        df_impact = df_impact.sort_values(by='Populasi_Terdampak', ascending=True)

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.barh(df_impact['Kabupaten'], df_impact['Populasi_Terdampak'], color='crimson')
        ax.set_xlabel('Jumlah Jiwa Terpapar')
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        st.pyplot(fig)
    except FileNotFoundError:
        st.warning("Menunggu data CSV... Pastikan script ekstrak data (Cell 10) sudah dijalankan terlebih dahulu.")

st.markdown("---")
st.caption("© 2026 Geosoftware Training - Dikembangkan dengan Python, Google Earth Engine & Streamlit")
