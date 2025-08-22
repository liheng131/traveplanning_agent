# ... (原有Django设置) ...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'rest_framework',  # 添加
    'corsheaders',  # 添加
    'api',  # 添加你的 app
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 添加在最前面
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'backend.urls'
# ... (原有Django设置) ...
SECRET_KEY = 'django-insecure-a)s@m3#l-b5$v(2+qf!z_y8@x&c_p*k!n#t!$j9*^u'
DEBUG = True
STATIC_URL = 'static/'
# 添加 CORS 配置，允许前端访问
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173", "http://localhost:5173"
]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:5173", "http://localhost:5173"
]
