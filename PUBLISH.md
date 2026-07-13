# Как опубликовать (один раз)

## GitHub Pages (бесплатно, постоянная ссылка)

1. Откройте https://github.com/german228g/Reposi/settings/pages
2. В **Build and deployment** → Source выберите **GitHub Actions**
3. Сохраните — через 1–2 минуты игра будет здесь:

   **https://german228g.github.io/Reposi/**

4. На iPhone: Safari → ссылка → **▶ ИГРАТЬ**
5. **Поделиться** → **На экран Домой** → готово!

## Локально (без интернета, тот же Wi‑Fi)

```bash
chmod +x serve-ios.sh
./serve-ios.sh
```

Откройте напечатанный адрес на iPhone в Safari.

## Netlify (альтернатива)

1. https://app.netlify.com → Import from Git
2. Выберите репозиторий `Reposi`
3. Deploy — получите ссылку вида `https://xxx.netlify.app`
