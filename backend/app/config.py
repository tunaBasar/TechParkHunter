from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "TechPark Hunter"
    DEBUG: bool = True
    DATA_DIR: str = "data"
    DATABASE_URL: str = "techpark_hunter.db"

    # Gmail SMTP ile e-posta gönderimi için. GMAIL_APP_PASSWORD, Google
    # hesabında 2FA açıp oluşturulan bir "Uygulama Şifresi"dir (normal Google
    # şifresi değildir). Bu ayarlar boşsa e-posta gönderme özelliği devre
    # dışı kalır ve anlamlı bir hata mesajı döner.
    GMAIL_ADDRESS: str = ""
    GMAIL_APP_PASSWORD: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
