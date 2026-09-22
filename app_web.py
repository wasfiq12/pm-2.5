import streamlit as st
import ee
import folium
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
from google.oauth2 import service_account


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Dashboard PM2.5 Kalimantan Tengah",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* =========================
       GLOBAL
    ========================= */

    .stApp {
        background-color: #f5f7fb;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        color: #12355b;
    }

    /* =========================
       HEADER
       ========================= */

    .dashboard-header {
        background: linear-gradient(
            135deg,
            #0b3d91 0%,
            #1565c0 50%,
            #0288d1 100%
        );

        padding: 28px 32px;
        border-radius: 18px;
        margin-bottom: 20px;

        box-shadow:
            0 8px 25px rgba(21, 101, 192, 0.18);
    }

    .dashboard-title {
        color: white;
        font-size: 32px;
        font-weight: 750;
        margin-bottom: 6px;
    }

    .dashboard-subtitle {
        color: rgba(255,255,255,0.90);
        font-size: 15px;
        margin-bottom: 0;
    }

    .dashboard-badge {
        display: inline-block;
        margin-top: 15px;
        padding: 6px 13px;
        border-radius: 20px;
        background: rgba(255,255,255,0.16);
        color: white;
        font-size: 13px;
        border: 1px solid rgba(255,255,255,0.22);
    }


    /* =========================
       KPI CARDS
       ========================= */

    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 22px;
    }

    .kpi-card {
        flex: 1;
        background: white;
        border-radius: 14px;
        padding: 18px 20px;

        border: 1px solid #e4eaf2;

        box-shadow:
            0 4px 15px rgba(15, 45, 80, 0.06);
    }

    .kpi-icon {
        font-size: 22px;
        margin-bottom: 7px;
    }

    .kpi-label {
        color: #6b7785;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }

    .kpi-value {
        color: #12355b;
        font-size: 21px;
        font-weight: 750;
        margin-top: 3px;
    }


    /* =========================
       SECTION HEADER
       ========================= */

    .section-header {
        background: white;
        padding: 14px 18px;
        border-radius: 12px;
        border-left: 5px solid #1565c0;

        margin-bottom: 12px;

        box-shadow:
            0 3px 12px rgba(15, 45, 80, 0.05);
    }

    .section-title {
        font-size: 19px;
        font-weight: 700;
        color: #12355b;
    }

    .section-description {
        font-size: 12px;
        color: #718096;
        margin-top: 3px;
    }


    /* =========================
       STATISTIC CARD
       ========================= */

    .stat-card {
        background: white;
        padding: 18px;
        border-radius: 14px;

        border: 1px solid #e4eaf2;

        box-shadow:
            0 4px 15px rgba(15, 45, 80, 0.06);

        margin-bottom: 15px;
    }

    .stat-title {
        font-size: 17px;
        font-weight: 700;
        color: #12355b;
    }

    .stat-description {
        color: #718096;
        font-size: 12px;
        line-height: 1.5;
        margin-top: 5px;
    }


    /* =========================
       LEGEND
       ========================= */

    .legend-card {
        background: white;
        border-radius: 14px;
        padding: 20px;

        border: 1px solid #e4eaf2;

        box-shadow:
            0 4px 15px rgba(15, 45, 80, 0.05);

        margin-top: 15px;
    }

    .legend-title {
        font-size: 17px;
        font-weight: 700;
        color: #12355b;
        margin-bottom: 15px;
    }

    .legend-item {
        margin-bottom: 17px;
    }

    .legend-name {
        font-size: 13px;
        font-weight: 650;
        color: #334155;
        margin-bottom: 6px;
    }

    .legend-gradient {
        height: 11px;
        border-radius: 10px;
        width: 100%;
    }

    .legend-scale {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        color: #718096;
        margin-top: 4px;
    }


    /* =========================
       INFO BOX
       ========================= */

    .info-box {
        background: #eef6ff;
        border: 1px solid #cfe5ff;
        border-radius: 12px;
        padding: 14px 16px;

        color: #24527a;
        font-size: 13px;

        line-height: 1.55;
    }


    /* =========================
       FOOTER
       ========================= */

    .footer {
        margin-top: 35px;
        padding: 20px;
        border-top: 1px solid #dce3ec;

        text-align: center;
        color: #8a96a3;
        font-size: 12px;
    }

    .footer strong {
        color: #526477;
    }


    /* =========================
       STREAMLIT ELEMENT
       ========================= */

    div[data-testid="stExpander"] {
        border: none;
        background: transparent;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# EARTH ENGINE INITIALIZATION
# ============================================================

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
        project="wasfiq12"
    )

except Exception as e:

    st.error(
        f"""
        **Earth Engine gagal diinisialisasi**

        Detail:
        `{e}`
        """
    )

    st.stop()


# ============================================================
# PARAMETERS
# ============================================================

roi = ee.FeatureCollection(
    'projects/wasfiq12/assets/Kalteng'
)

start_date = '2026-08-01'
end_date = '2026-08-28'


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="dashboard-header">

    <div class="dashboard-title">
        🌫️ Dashboard Kualitas Udara
    </div>

    <div class="dashboard-subtitle">
        Prediksi PM2.5 dan Analisis Risiko Paparan Penduduk
        di Provinsi Kalimantan Tengah
    </div>

    <div class="dashboard-badge">
        🛰️ Google Earth Engine &nbsp;|&nbsp;
        🤖 Random Forest &nbsp;|&nbsp;
        📊 Zonal Statistics
    </div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# KPI CARDS
# ============================================================

st.markdown("""
<div class="kpi-container">

    <div class="kpi-card">
        <div class="kpi-icon">📍</div>
        <div class="kpi-label">Wilayah Analisis</div>
        <div class="kpi-value">Kalimantan Tengah</div>
    </div>

    <div class="kpi-card">
        <div class="kpi-icon">📅</div>
        <div class="kpi-label">Periode Data</div>
        <div class="kpi-value">1–28 Agustus 2026</div>
    </div>

    <div class="kpi-card">
        <div class="kpi-icon">🤖</div>
        <div class="kpi-label">Model</div>
        <div class="kpi-value">Random Forest</div>
    </div>

    <div class="kpi-card">
        <div class="kpi-icon">🛰️</div>
        <div class="kpi-label">Data Penginderaan Jauh</div>
        <div class="kpi-value">Sentinel-5P + ERA5</div>
    </div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# MAIN CONTENT
# ============================================================

col_map, col_stat = st.columns(
    [7.5, 2.5],
    gap="large"
)


# ============================================================
# MAP
# ============================================================

with col_map:

    st.markdown("""
    <div class="section-header">

        <div class="section-title">
            🗺️ Peta Interaktif Sebaran PM2.5
        </div>

        <div class="section-description">
            Gunakan kontrol layer di kanan atas peta untuk menampilkan
            parameter meteorologi, kualitas udara, dan hasil prediksi PM2.5.
        </div>

    </div>
    """, unsafe_allow_html=True)


    map_dash = folium.Map(
        location=[-1.5, 113.5],
        zoom_start=6,
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap",
        max_zoom=20
    )


    # ========================================================
    # GEE LAYER FUNCTION
    # ========================================================

    def add_ee_layer(
        self,
        ee_image_object,
        vis_params,
        name,
        show=True
    ):

        map_id_dict = ee.Image(
            ee_image_object
        ).getMapId(vis_params)

        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Map Data © Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            show=show
        ).add_to(self)


    folium.Map.add_ee_layer = add_ee_layer


    # ========================================================
    # A. DATA METEOROLOGI
    # ========================================================

    era5 = (
        ee.ImageCollection(
            "ECMWF/ERA5_LAND/DAILY_AGGR"
        )
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .mean()
        .clip(roi)
    )


    map_dash.add_ee_layer(
        era5.select('u_component_of_wind_10m'),
        {
            'min': -3.0,
            'max': 3.0,
            'palette': [
                'blue',
                'white',
                'red'
            ]
        },
        'Wind U',
        show=False
    )


    map_dash.add_ee_layer(
        era5.select('temperature_2m'),
        {
            'min': 295,
            'max': 305,
            'palette': [
                'blue',
                'cyan',
                'green',
                'yellow',
                'red'
            ]
        },
        'Temperature 2m',
        show=False
    )


    # ========================================================
    # B. DATA KUALITAS UDARA
    # ========================================================

    no2 = (
        ee.ImageCollection(
            "COPERNICUS/S5P/NRTI/L3_NO2"
        )
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .mean()
        .clip(roi)
    )


    map_dash.add_ee_layer(
        no2.select(
            'NO2_column_number_density'
        ),
        {
            'min': 0,
            'max': 0.0002,
            'palette': [
                'black',
                'blue',
                'purple',
                'cyan',
                'green',
                'yellow',
                'red'
            ]
        },
        'NO₂',
        show=False
    )


    hcho = (
        ee.ImageCollection(
            "COPERNICUS/S5P/NRTI/L3_HCHO"
        )
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .mean()
        .clip(roi)
    )


    map_dash.add_ee_layer(
        hcho.select(
            'tropospheric_HCHO_column_number_density'
        ),
        {
            'min': 0,
            'max': 0.0005,
            'palette': [
                'black',
                'blue',
                'purple',
                'cyan',
                'green',
                'yellow',
                'red'
            ]
        },
        'HCHO',
        show=False
    )


    # ========================================================
    # C. AEROSOL INDEX
    # ========================================================

    ai_raw = (
        ee.ImageCollection(
            "COPERNICUS/S5P/NRTI/L3_AER_AI"
        )
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .mean()
        .clip(roi)
    )


    vis_ai = {
        'min': 0.0,
        'max': 1.5,
        'palette': [
            'black',
            'blue',
            'purple',
            'cyan',
            'green',
            'yellow',
            'red'
        ]
    }


    map_dash.add_ee_layer(
        ai_raw.select(
            'absorbing_aerosol_index'
        ),
        vis_ai,
        'Aerosol Index',
        show=False
    )


    # ========================================================
    # D. RANDOM FOREST PM2.5
    # ========================================================

    with st.spinner(
        "Memproses data dan Random Forest..."
    ):

        ai_col = (
            ee.ImageCollection(
                'COPERNICUS/S5P/NRTI/L3_AER_AI'
            )
            .filterBounds(roi)
            .filterDate(
                start_date,
                end_date
            )
            .select(
                'absorbing_aerosol_index'
            )
            .mean()
        )


        predictors = (
            ai_col
            .addBands(era5)
            .addBands(no2)
            .addBands(hcho)
        )


        predictors_renamed = predictors.select(

            [
                'absorbing_aerosol_index',
                'temperature_2m',
                'u_component_of_wind_10m',
                'NO2_column_number_density',
                'tropospheric_HCHO_column_number_density'
            ],

            [
                'Aerosol_Index',
                'Temperature_2m',
                'Wind_U',
                'NO2_Density',
                'HCHO_Density'
            ]
        )


        # ====================================================
        # TRAINING DATA
        # ====================================================

        df_train = pd.read_csv(
            'training_data_pm25.csv'
        )


        ee_features = []


        for index, row in df_train.iterrows():

            feat = ee.Feature(

                ee.Geometry.Point(
                    [
                        row['longitude'],
                        row['latitude']
                    ]
                ),

                {
                    'Aerosol_Index':
                        row['Aerosol_Index'],

                    'Temperature_2m':
                        row['Temperature_2m'],

                    'Wind_U':
                        row['Wind_U'],

                    'NO2_Density':
                        row['NO2_Density'],

                    'HCHO_Density':
                        row['HCHO_Density'],

                    'Actual_PM25':
                        row['Actual_PM25']
                }
            )

            ee_features.append(feat)


        fc_training = ee.FeatureCollection(
            ee_features
        )


        # ====================================================
        # RANDOM FOREST
        # ====================================================

        features = [
            'Aerosol_Index',
            'Temperature_2m',
            'Wind_U',
            'NO2_Density',
            'HCHO_Density'
        ]


        classifier = (

            ee.Classifier
            .smileRandomForest(10)
            .setOutputMode('REGRESSION')
            .train(

                features=fc_training,

                classProperty='Actual_PM25',

                inputProperties=features
            )
        )


        predicted_pm25 = (
            predictors_renamed
            .classify(classifier)
            .clip(roi)
        )


        # ====================================================
        # PM2.5 MAP
        # ====================================================

        vis_pm25 = {

            'min': 0,
            'max': 100,

            'palette': [
                '008000',
                'FFFF00',
                'FFA500',
                'FF0000',
                '800080'
            ]
        }


        map_dash.add_ee_layer(

            predicted_pm25,

            vis_pm25,

            'Prediksi PM2.5',

            show=True
        )


        # ====================================================
        # DANGER ZONE
        # ====================================================

        danger_zone = predicted_pm25.gt(40)

        danger_masked = (
            danger_zone
            .updateMask(
                danger_zone.eq(1)
            )
        )


        map_dash.add_ee_layer(

            danger_masked,

            {
                'min': 0,
                'max': 1,
                'palette': ['red']
            },

            'Zona PM2.5 > 40',

            show=True
        )


    # ========================================================
    # ADMINISTRATIVE BOUNDARY
    # ========================================================

    empty_image = ee.Image().byte()

    outline = empty_image.paint(
        featureCollection=roi,
        color=1,
        width=2
    )


    map_dash.add_ee_layer(

        outline,

        {
            'palette': ['black']
        },

        'Batas Administrasi Kalteng',

        show=True
    )


    map_dash.add_child(
        folium.LayerControl(
            collapsed=False
        )
    )


    # ========================================================
    # DISPLAY MAP
    # ========================================================

    map_html = map_dash._repr_html_()

    components.html(
        map_html,
        height=650
    )


# ============================================================
# STATISTICS
# ============================================================

with col_stat:

    st.markdown("""
    <div class="section-header">

        <div class="section-title">
            📊 Statistik Dampak
        </div>

        <div class="section-description">
            Estimasi populasi yang berada pada area
            dengan PM2.5 > 40 µg/m³.
        </div>

    </div>
    """, unsafe_allow_html=True)


    try:

        df_impact = pd.read_csv(
            'data_dampak_kalteng.csv'
        )


        df_impact = df_impact.sort_values(
            by='Populasi_Terdampak',
            ascending=True
        )


        total_population = int(
            df_impact['Populasi_Terdampak'].sum()
        )


        max_population = int(
            df_impact['Populasi_Terdampak'].max()
        )


        affected_area = len(
            df_impact
        )


        # ====================================================
        # SMALL KPI
        # ====================================================

        st.markdown(
            f"""
            <div class="stat-card">

                <div class="kpi-label">
                    TOTAL ESTIMASI TERPAPAR
                </div>

                <div class="kpi-value">
                    {total_population:,}
                </div>

                <div class="stat-description">
                    jiwa berdasarkan data zonal statistics
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            f"""
            <div class="stat-card">

                <div class="kpi-label">
                    KABUPATEN / WILAYAH
                </div>

                <div class="kpi-value">
                    {affected_area}
                </div>

                <div class="stat-description">
                    wilayah yang tercatat pada dataset
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # BAR CHART
        # ====================================================

        fig, ax = plt.subplots(
            figsize=(6, 7)
        )


        ax.barh(

            df_impact['Kabupaten'],

            df_impact[
                'Populasi_Terdampak'
            ],

            height=0.65
        )


        ax.set_xlabel(
            'Jumlah Jiwa Terpapar',
            fontsize=10
        )


        ax.set_ylabel(
            '',
            fontsize=10
        )


        ax.tick_params(
            axis='y',
            labelsize=8
        )


        ax.tick_params(
            axis='x',
            labelsize=8
        )


        ax.grid(
            axis='x',
            linestyle='--',
            alpha=0.3
        )


        ax.set_axisbelow(True)


        for spine in [
            'top',
            'right',
            'left'
        ]:

            ax.spines[
                spine
            ].set_visible(False)


        fig.tight_layout()


        st.pyplot(
            fig,
            use_container_width=True
        )


    except FileNotFoundError:

        st.warning(
            """
            Data statistik belum tersedia.

            Pastikan file
            `data_dampak_kalteng.csv`
            sudah berada di repository.
            """
        )


# ============================================================
# LEGEND
# ============================================================

st.markdown(
    """
    <div class="legend-card">

        <div class="legend-title">
            🎨 Legenda Parameter
        </div>

        <div class="legend-item">

            <div class="legend-name">
                Prediksi PM2.5 (µg/m³)
            </div>

            <div
                class="legend-gradient"
                style="
                    background:
                    linear-gradient(
                        to right,
                        #008000,
                        #FFFF00,
                        #FFA500,
                        #FF0000,
                        #800080
                    );
                ">
            </div>

            <div class="legend-scale">
                <span>0</span>
                <span>20</span>
                <span>40</span>
                <span>60</span>
                <span>80+</span>
            </div>

        </div>


        <div class="legend-item">

            <div class="legend-name">
                Aerosol Index
            </div>

            <div
                class="legend-gradient"
                style="
                    background:
                    linear-gradient(
                        to right,
                        black,
                        blue,
                        purple,
                        cyan,
                        green,
                        yellow,
                        red
                    );
                ">
            </div>

            <div class="legend-scale">
                <span>0.0</span>
                <span>0.5</span>
                <span>1.0</span>
                <span>1.5+</span>
            </div>

        </div>


        <div class="legend-item">

            <div class="legend-name">
                Suhu 2 m (Kelvin)
            </div>

            <div
                class="legend-gradient"
                style="
                    background:
                    linear-gradient(
                        to right,
                        blue,
                        cyan,
                        green,
                        yellow,
                        red
                    );
                ">
            </div>

            <div class="legend-scale">
                <span>295 K</span>
                <span>300 K</span>
                <span>305 K</span>
            </div>

        </div>


        <div class="legend-item">

            <div class="legend-name">
                Komponen Angin U (m/s)
            </div>

            <div
                class="legend-gradient"
                style="
                    background:
                    linear-gradient(
                        to right,
                        blue,
                        white,
                        red
                    );
                ">
            </div>

            <div class="legend-scale">
                <span>-3.0</span>
                <span>0</span>
                <span>+3.0</span>
            </div>

        </div>


        <div class="legend-item">

            <div class="legend-name">
                NO₂ / HCHO Density
            </div>

            <div
                class="legend-gradient"
                style="
                    background:
                    linear-gradient(
                        to right,
                        black,
                        blue,
                        purple,
                        cyan,
                        green,
                        yellow,
                        red
                    );
                ">
            </div>

            <div class="legend-scale">
                <span>Rendah</span>
                <span>Tinggi</span>
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# INFORMATION
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">

    <strong>ℹ️ Tentang Dashboard</strong><br>

    Dashboard ini menampilkan estimasi spasial PM2.5 menggunakan
    pendekatan <strong>Random Forest Machine Learning</strong>
    dengan kombinasi parameter Aerosol Index, suhu udara,
    komponen angin U, NO₂, dan HCHO.

    Data penginderaan jauh dan meteorologi diproses menggunakan
    <strong>Google Earth Engine</strong>, kemudian divisualisasikan
    secara interaktif menggunakan Folium.

</div>
""", unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">

    <strong>Dashboard Kualitas Udara Kalimantan Tengah</strong><br>

    Google Earth Engine • Python • Random Forest • Streamlit • Folium

    <br><br>

    © 2026 Geosoftware Training

</div>
""", unsafe_allow_html=True)
