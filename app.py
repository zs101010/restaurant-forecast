

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Restaurant Forecast",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ФАЙЛ ДЛЯ ХРАНЕНИЯ ДАННЫХ ===
DATA_FILE = "restaurant_data.json"

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ===
def load_user_data():
    """Загружает данные из JSON-файла"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "historical_guests": {},  # словарь {дата: количество гостей}
        "products": {  # продукты и их расход
            "мясо": {"unit": "кг", "per_guest": 0.2},
            "овощи": {"unit": "кг", "per_guest": 0.15},
            "хлеб": {"unit": "шт", "per_guest": 0.5},
            "напитки": {"unit": "л", "per_guest": 0.3}
        }
    }

def save_user_data(data):
    """Сохраняет данные в JSON-файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === ЗАГРУЗКА ДАННЫХ ===
user_data = load_user_data()

# === БОКОВАЯ ПАНЕЛЬ (АДМИНИСТРИРОВАНИЕ) ===
with st.sidebar:
    st.header("⚙️ Управление данными")
    
    admin_mode = st.checkbox("Режим редактирования", help="Включите, чтобы вносить изменения")
    
    if admin_mode:
        st.subheader("📊 Ввод данных о посетителях")
        
        # Ручной ввод
        col1, col2 = st.columns(2)
        with col1:
            manual_date = st.date_input("Дата", datetime.now().date())
        with col2:
            manual_guests = st.number_input("Количество гостей", min_value=0, step=5)
        
        if st.button("➕ Добавить/обновить данные"):
            date_str = manual_date.strftime("%Y-%m-%d")
            user_data["historical_guests"][date_str] = manual_guests
            save_user_data(user_data)
            st.success(f"Данные на {date_str} сохранены!")
            st.rerun()
        
        st.divider()
        
        # Загрузка CSV-файла
        st.subheader("📁 Загрузка таблицы")
        uploaded_file = st.file_uploader("Выберите CSV или Excel файл", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("Предпросмотр:")
                st.dataframe(df_upload.head())
                
                # Ожидаем колонки: date, guests
                if st.button("Загрузить данные из файла"):
                    for _, row in df_upload.iterrows():
                        if 'date' in df_upload.columns and 'guests' in df_upload.columns:
                            date_str = pd.to_datetime(row['date']).strftime("%Y-%m-%d")
                            user_data["historical_guests"][date_str] = int(row['guests'])
                    save_user_data(user_data)
                    st.success("Данные загружены!")
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка: {e}")
        
        st.divider()
        
        # Настройка продуктов
        st.subheader("🥩 Настройка расхода продуктов")
        
        for product, info in user_data["products"].items():
            col1, col2 = st.columns([2, 1])
            with col1:
                new_per_guest = st.number_input(
                    f"{product} (расход на 1 гостя, {info['unit']})",
                    value=float(info["per_guest"]),
                    step=0.01,
                    key=f"prod_{product}"
                )
            with col2:
                st.write(f"ед.: {info['unit']}")
            user_data["products"][product]["per_guest"] = new_per_guest
        
        if st.button("💾 Сохранить настройки продуктов"):
            save_user_data(user_data)
            st.success("Настройки сохранены!")
        
        st.divider()
        
        # Сброс данных
        if st.button("🗑️ Сбросить все данные", type="secondary"):
            user_data = {
                "historical_guests": {},
                "products": {
                    "мясо": {"unit": "кг", "per_guest": 0.2},
                    "овощи": {"unit": "кг", "per_guest": 0.15},
                    "хлеб": {"unit": "шт", "per_guest": 0.5},
                    "напитки": {"unit": "л", "per_guest": 0.3}
                }
            }
            save_user_data(user_data)
            st.warning("Все данные сброшены!")
            st.rerun()

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
st.title("🍽️ Restaurant Load Forecast")
st.caption("Прогноз загрузки ресторана с возможностью ручного ввода данных")

# === ОГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ ===
with st.expander("⚖️ Ограничение ответственности"):
    st.markdown("""
    **Демонстрационная версия.** Прогнозы носят информационный характер.
    Решения о закупках принимаются пользователем самостоятельно.
    """)

# === ПОСТРОЕНИЕ ПРОГНОЗА ===
def generate_forecast():
    """Генерирует прогноз на основе исторических и ручных данных"""
    
    # Базовые значения по дням недели
    dow_factors = [0.7, 0.8, 0.85, 0.9, 1.0, 1.3, 1.1]
    
    # Собираем историю
    dates = []
    guests_actual = []
    
    for date_str, guests in user_data["historical_guests"].items():
        dates.append(pd.to_datetime(date_str))
        guests_actual.append(guests)
    
    # Если есть история, считаем базовую среднюю
    if len(guests_actual) > 0:
        base_avg = np.mean(guests_actual)
    else:
        base_avg = 100  # значение по умолчанию
    
    # Прогноз на 7 дней
    forecast_data = []
    today = datetime.now().date()
    
    for i in range(7):
        forecast_date = today + timedelta(days=i)
        dow = forecast_date.weekday()
        
        # Прогноз = среднее * коэффициент дня недели
        predicted = int(base_avg * dow_factors[dow])
        
        forecast_data.append({
            "date": forecast_date,
            "day_name": ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"][dow],
            "predicted_guests": predicted,
            "recommendation": get_recommendation(predicted, base_avg)
        })
    
    return forecast_data, base_avg

def get_recommendation(predicted, avg):
    if predicted > avg * 1.2:
        return "🔴 Высокий спрос (+30% продуктов)"
    elif predicted > avg * 1.05:
        return "🟡 Повышенный спрос (+15% продуктов)"
    elif predicted < avg * 0.8:
        return "🟢 Низкий спрос (-20% скоропорта)"
    else:
        return "✅ Стандартный режим"

# === ВКЛАДКА 1: ПРОГНОЗ ===
forecast_data, base_avg = generate_forecast()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Прогноз", "📅 Таблица данных", "🥩 Расход продуктов", "ℹ️ Помощь"])

with tab1:
    st.subheader("Прогноз на неделю")
    
    # График
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{d['date'].day}.{d['date'].month}\n{d['day_name']}" for d in forecast_data],
        y=[d['predicted_guests'] for d in forecast_data],
        marker_color=['#FF6B6B' if 'Высокий' in d['recommendation'] else '#4ECDC4' for d in forecast_data],
        text=[d['predicted_guests'] for d in forecast_data],
        textposition='auto',
    ))
    fig.update_layout(
        title="Ожидаемое количество гостей",
        yaxis_title="Гостей",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Карточки по дням
    cols = st.columns(7)
    for i, day in enumerate(forecast_data):
        with cols[i]:
            st.metric(
                label=f"{day['day_name']} {day['date'].day}.{day['date'].month}",
                value=f"{day['predicted_guests']} чел.",
                delta="высокий" if "Высокий" in day['recommendation'] else ("низкий" if "Низкий" in day['recommendation'] else "норма")
            )
            st.caption(day['recommendation'])

with tab2:
    st.subheader("Исторические данные")
    
    if user_data["historical_guests"]:
        df_history = pd.DataFrame([
            {"Дата": date, "Гостей": guests}
            for date, guests in user_data["historical_guests"].items()
        ]).sort_values("Дата", ascending=False)
        
        st.dataframe(df_history, use_container_width=True)
        
        # График истории
        fig_hist = px.line(
            df_history.sort_values("Дата"),
            x="Дата", y="Гостей",
            title="Динамика посещаемости"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Пока нет исторических данных. Добавьте их в боковой панели →")
    
    # Статистика
    if len(user_data["historical_guests"]) > 0:
        values = list(user_data["historical_guests"].values())
        st.metric("Среднее количество гостей", f"{int(np.mean(values))} чел.")

with tab3:
    st.subheader("Расчет закупок продуктов")
    
    # Выбираем день для расчета
    selected_day_idx = st.selectbox(
        "Выберите день для расчета закупок:",
        range(7),
        format_func=lambda x: f"{forecast_data[x]['day_name']} {forecast_data[x]['date'].day}.{forecast_data[x]['date'].month} — {forecast_data[x]['predicted_guests']} гостей"
    )
    
    selected = forecast_data[selected_day_idx]
    guests_count = selected['predicted_guests']
    
    st.subheader(f"📋 Закупки на {selected['date'].day}.{selected['date'].month}")
    
    # Таблица продуктов
    product_data = []
    for product, info in user_data["products"].items():
        amount = guests_count * info["per_guest"]
        product_data.append({
            "Продукт": product,
            "Расход на 1 гостя": f"{info['per_guest']} {info['unit']}",
            "Всего на {guests_count} гостей": f"{amount:.1f} {info['unit']}"
        })
    
    df_products = pd.DataFrame(product_data)
    st.table(df_products)
    
    # Рекомендация по закупкам
    if "Высокий" in selected['recommendation']:
        st.warning("⚠️ Внимание: ожидается высокий спрос! Рекомендуется закупить на 30% больше скоропортящихся продуктов.")
    elif "Низкий" in selected['recommendation']:
        st.info("ℹ️ Ожидается низкий спрос. Рекомендуется сократить закупки скоропорта на 20%.")

with tab4:
    st.subheader("Как пользоваться")
    
    st.markdown("""
    ### 📝 Ручной ввод данных
    
    1. Откройте **боковую панель** (значок `>` слева)
    2. Включите **"Режим редактирования"**
    3. Вводите данные о посетителях:
       - **Вручную** — выберите дату и количество гостей
       - **Файлом** — загрузите CSV/Excel с колонками `date` и `guests`
    4. Настройте **расход продуктов** под ваше меню
    
    ### 📊 Прогноз
    
    - Модель анализирует введенные вами данные
    - Учитывает день недели
    - Показывает рекомендации по закупкам
    
    ### 🔄 Обновление
    
    - После добавления новых данных прогноз пересчитывается автоматически
    - Чем больше истории, тем точнее прогноз
    """)

# === ФУТЕР ===
st.divider()
st.caption("© 2025 Restaurant Forecast | Ручной ввод данных | Прогнозы не являются гарантией")
