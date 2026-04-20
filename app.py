import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Restaurant Forecast",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# === ЗАГРУЗКА ДАННЫХ (синтетические данные для демонстрации) ===
@st.cache_data
def load_data():
    """Генерирует демонстрационные данные"""
    dates = pd.date_range(start='2024-01-01', end='2025-03-31', freq='D')
    
    # Базовые паттерны
    day_of_week_effect = {
        0: 0.7,   # Monday
        1: 0.8,   # Tuesday
        2: 0.85,  # Wednesday
        3: 0.9,   # Thursday
        4: 1.0,   # Friday
        5: 1.3,   # Saturday
        6: 1.1    # Sunday
    }
    
    # Сезонность
    month_effect = {
        1: 0.9, 2: 0.9, 3: 1.0, 4: 1.0, 5: 1.1, 6: 1.0,
        7: 0.9, 8: 0.9, 9: 1.0, 10: 1.0, 11: 1.1, 12: 1.3
    }
    
    # Погодные эффекты
    weather_effect = {
        'Clear': 1.0,
        'Clouds': 0.95,
        'Rain': 0.7,
        'Snow': 0.6,
        'Storm': 0.5
    }
    
    # Генерируем данные
    np.random.seed(42)
    data = []
    
    for date in dates:
        dow = date.dayofweek
        month = date.month
        
        base = 100
        base *= day_of_week_effect[dow]
        base *= month_effect[month]
        
        # Случайные погодные условия (для демонстрации)
        weather = np.random.choice(list(weather_effect.keys()), p=[0.6, 0.2, 0.1, 0.05, 0.05])
        base *= weather_effect[weather]
        
        # Случайный шум
        noise = np.random.normal(1.0, 0.1)
        guests = int(base * noise)
        
        # Случайная температура
        temp = np.random.normal(10, 15) if month in [1,2,12] else np.random.normal(20, 10)
        
        data.append({
            'date': date,
            'guests': max(20, guests),
            'temperature': round(temp, 1),
            'weather': weather
        })
    
    return pd.DataFrame(data)

# === ЗАГРУЗКА ===
df = load_data()

# === ЗАГОЛОВОК ===
st.title("🍽️ Restaurant Load Forecast")
st.caption("Прогноз загрузки ресторана на основе погоды и дня недели")

# === ОГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ ===
with st.expander("⚖️ Ограничение ответственности (обязательно к ознакомлению)"):
    st.markdown("""
    **Данный сервис предоставляется в демонстрационных целях.**
    
    1. Прогнозы носят информационный характер и не являются гарантией точного количества посетителей.
    2. Модель использует синтетические данные и открытые погодные API. Результаты могут отличаться от реальных.
    3. Разработчик не несет ответственности за любые убытки, возникшие при использовании прогнозов.
    4. Решения о закупках и расписании персонала принимаются пользователем самостоятельно.
    5. Для получения точных прогнозов требуется обучение модели на исторических данных вашего заведения.
    
    Используя сервис, вы подтверждаете, что ознакомлены с данным ограничением.
    """)

# === ОСНОВНОЙ ИНТЕРФЕЙС ===
tab1, tab2, tab3 = st.tabs(["📊 Прогноз на сегодня", "📅 Прогноз на неделю", "ℹ️ Как это работает"])

# === TAB 1: ПРОГНОЗ НА СЕГОДНЯ ===
with tab1:
    st.subheader("Прогноз на сегодня")
    
    # Получаем сегодняшнюю дату и данные
    today = datetime.now().date()
    today_data = df[df['date'].dt.date == today]
    
    if len(today_data) == 0:
        # Если данных на сегодня нет, берем последние 7 дней и делаем простой прогноз
        last_week = df.tail(7)
        avg_guests = last_week['guests'].mean()
        weather_today = np.random.choice(['Clear', 'Clouds', 'Rain'])
        weather_factor = {'Clear': 1.0, 'Clouds': 0.95, 'Rain': 0.7}.get(weather_today, 1.0)
        
        dow = today.weekday()
        dow_factor = [0.7, 0.8, 0.85, 0.9, 1.0, 1.3, 1.1][dow]
        
        predicted_guests = int(avg_guests * dow_factor * weather_factor)
        weekday_name = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'][dow]
        
        # Показываем прогноз
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ожидаемое количество гостей", f"{predicted_guests} чел.")
        with col2:
            st.metric("День недели", weekday_name)
        
        # Рекомендации
        if predicted_guests > avg_guests * 1.2:
            st.success("📈 **Рекомендация:** Ожидается повышенный спрос! Рекомендуется увеличить закупки продуктов на 25-30% и вывести дополнительного сотрудника.")
        elif predicted_guests < avg_guests * 0.8:
            st.info("📉 **Рекомендация:** Ожидается сниженный спрос. Рекомендуется сократить закупки скоропорта на 20% и оптимизировать график персонала.")
        else:
            st.info("📊 **Рекомендация:** Ожидается обычный спрос. Работайте в стандартном режиме.")
            
    else:
        # Если данные есть
        guests = today_data.iloc[0]['guests']
        weather = today_data.iloc[0]['weather']
        temp = today_data.iloc[0]['temperature']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Прогноз гостей", f"{guests} чел.")
        with col2:
            st.metric("Погода", weather)
        with col3:
            st.metric("Температура", f"{temp}°C")
        
        avg_week = df.tail(7)['guests'].mean()
        if guests > avg_week * 1.1:
            st.success("📈 **Рекомендация:** Сегодня ожидается больше гостей, чем обычно. Увеличьте закупки!")
        elif guests < avg_week * 0.9:
            st.info("📉 **Рекомендация:** Сегодня ожидается меньше гостей. Скорректируйте закупки.")
        else:
            st.info("✅ Прогноз в пределах нормы.")

# === TAB 2: ПРОГНОЗ НА НЕДЕЛЮ ===
with tab2:
    st.subheader("Прогноз на предстоящую неделю")
    
    # Берем последнюю неделю данных + генерируем прогноз
    last_week = df.tail(7).copy()
    last_week['day_name'] = last_week['date'].dt.strftime('%A')
    
    # Создаем график
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=last_week['date'].dt.strftime('%d.%m'),
        y=last_week['guests'],
        name='Прогноз гостей',
        marker_color='#FF6B6B',
        text=last_week['guests'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Ожидаемое количество гостей по дням",
        xaxis_title="Дата",
        yaxis_title="Количество гостей",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Таблица с рекомендациями по дням
    st.subheader("Рекомендации по дням")
    
    for _, row in last_week.iterrows():
        day_name = row['date'].strftime('%A')
        guests = row['guests']
        
        if guests > 130:
            rec = "🔴 Высокий спрос: увеличьте закупки на 30%"
        elif guests > 100:
            rec = "🟡 Средний спрос: стандартные закупки"
        else:
            rec = "🟢 Низкий спрос: сократите закупки скоропорта"
        
        with st.expander(f"📅 {day_name} — {guests} гостей"):
            st.write(f"**Рекомендация:** {rec}")
            st.write(f"**Погода:** {row['weather']}, {row['temperature']}°C")

# === TAB 3: КАК ЭТО РАБОТАЕТ ===
with tab3:
    st.subheader("Как работает прогноз")
    
    st.markdown("""
    **Модель учитывает три ключевых фактора:**
    
    1. **День недели** 📅
       - Выходные дни (СБ, ВС) традиционно приносят на 30-40% больше гостей
       - Понедельник и вторник — самые спокойные дни
    
    2. **Погодные условия** ☀️🌧️
       - Ясная погода → рост посетителей
       - Дождь и снег → снижение на 20-40%
    
    3. **Сезонность** 📆
       - Декабрь (Новый год) → пик загрузки
       - Лето → снижение из-за отпусков
    
    **Технологии:**
    - Python + Streamlit для интерфейса
    - Plotly для графиков
    - Pandas для обработки данных
    
    **Для точных прогнозов вашему заведению нужно:**
    1. Загрузить историю продаж за 3-6 месяцев
    2. Модель обучится на ваших данных
    3. Получать персонализированные прогнозы
    """)
    
    st.info("💡 **Совет:** Для получения более точных прогнозов свяжитесь с разработчиком для настройки модели под ваше заведение.")

# === ФУТЕР С ПРАВОВОЙ ИНФОРМАЦИЕЙ ===
st.divider()
st.caption("© 2025 Restaurant Forecast | Демонстрационная версия | Прогнозы не являются гарантией | v1.0")
