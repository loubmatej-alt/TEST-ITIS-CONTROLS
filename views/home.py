import streamlit as st
import base64
import urllib.request
from st_clickable_images import clickable_images

# 1. Funkce pro stažení obrázku a převod do Base64 (cachujeme, ať se nestahuje při každém kliknutí)
@st.cache_data
def get_image_base64(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            img_data = response.read()
            return "data:image/png;base64," + base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        return "" # Pokud by URL přestalo fungovat, nehodí to error

# Hide the sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>Welcome to the Data hub</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-top: 0rem; margin-bottom: 2rem;'>Select business:</p>", unsafe_allow_html=True)

# 2. Stažení log z internetu přímo do aplikace
itis_logo = get_image_base64("https://nelisa-public.fra1.cdn.digitaloceanspaces.com/itis-holding-a-s/logo.png")
vitronic_logo = get_image_base64("https://upload.wikimedia.org/wikipedia/commons/5/5e/Vitronic_Logo_%26_Claim_2019.jpg")

# 3. Zmenšené SVG karty s natvrdo vloženými obrázky
# Šířka je 330px, aby se bez problému vešly vedle sebe
svg_itis = f"""
<svg width="330" height="280" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="15" fill="#E6F0FA" stroke="#00509E" stroke-width="4"/>
  <image href="{itis_logo}" x="15" y="15" height="240" width="300"/>
  <text x="50%" y="240" font-size="14" font-family="sans-serif" fill="#333" text-anchor="middle">Data &amp; Reporting</text>
</svg>
"""

svg_vitronic = f"""
<svg width="330" height="280" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="15" fill="#E6F0FA" stroke="#071544" stroke-width="4"/>
  <image href="{vitronic_logo}" x="15" y="15" height="240" width="300"/>
  <text x="50%" y="240" font-size="14" font-family="sans-serif" fill="#333" text-anchor="middle">Logistics &amp; Operations</text>
</svg>
"""

# Převod samotných SVG do Base64
b64_itis = base64.b64encode(svg_itis.encode('utf-8')).decode('utf-8')
b64_vitronic = base64.b64encode(svg_vitronic.encode('utf-8')).decode('utf-8')

# 4. Vykreslení
clicked = clickable_images(
    paths=[
        f"data:image/svg+xml;base64,{b64_itis}",
        f"data:image/svg+xml;base64,{b64_vitronic}"
    ],
    titles=["Enter Itis Environment", "Enter Vitronic Environment"],
    div_style={"display": "flex", "justify-content": "center", "gap": "20px"}, # Zmenšená mezera
    img_style={
        "cursor": "pointer", 
        "border-radius": "15px", 
        "box-shadow": "2px 2px 10px rgba(0,0,0,0.1)",
        "transition": "transform 0.2s"
    }
)

# Hover efekt na zvednutí karty při najetí myší
st.markdown("""
    <style>
        img {
            transition: all 0.3s ease !important;
        }
        img:hover {
            transform: scale(1.05) translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.3) !important;
            filter: brightness(1.1);
        }
    </style>
""", unsafe_allow_html=True)

# 5. Routování
if clicked == 0:
    st.switch_page("views/itis/hub.py")
elif clicked == 1:
    st.switch_page("views/vitronic/hub.py")