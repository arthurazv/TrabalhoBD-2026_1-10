"""CSS customizado da aplicação (tema visual do NullBank)."""

CSS = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background-color: #0F0F1A;
        color: #E0E0FF;
    }

    .main-title {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF7676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        font-size: 2.5rem;
    }

    .subtitle {
        text-align: center;
        color: #8A8AAB;
        font-family: 'Inter', sans-serif;
        margin-bottom: 2rem;
    }

    .user-badge {
        background-color: #1A1A2E;
        border: 1px solid #3F3F5F;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Customizar abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #141424;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #252538;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #8A8AAB;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #FF7676;
        background-color: #1E1E32;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    </style>
"""