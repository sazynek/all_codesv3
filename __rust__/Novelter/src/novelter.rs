use fake::Fake;
use fake::faker::internet::en::UserAgent;
use futures::future::join_all;
use rand::Rng;
use regex::Regex;
use scraper::{Html, Selector};
use serde_json::Value;
use std::error::Error;
use std::vec;
use tokio::task::{JoinError, JoinHandle};

pub struct RanobesData {
    // Vec<u8>, String, i32, Vec<(String, Vec<u8>)
    pub img: Vec<u8>,
    pub img_path: String,
    pub title: String,
    pub total_chapters: i32,
    pub chapters: Vec<RanobesChapters>,
}
impl RanobesData {
    fn new(
        img: Vec<u8>,
        img_path: String,
        title: String,
        total_chapters: i32,
        chapters: Vec<RanobesChapters>,
    ) -> Self {
        Self {
            img,
            img_path,
            title,
            total_chapters,
            chapters,
        }
    }
}
pub struct RanobesChapters {
    pub title: String,
    pub content: Vec<u8>,
}
impl RanobesChapters {
    fn new(title: String, content: Vec<u8>) -> Self {
        Self { title, content }
    }
}
pub struct Ranobes {}
impl Ranobes {
    const DOMAIN: &'static str = "https://Ranobes.net";
    const URL: &'static str = "https://Ranobes.net/novels/";
    const PAGES_URL: &'static str = "https://Ranobes.net/novels/page/";
    // const PAGE_COUNT: u32 = 3;
    const BATCH_SIZE: u32 = 1;

    // Фабрика для создания уникальных клиентов
    pub fn create_client() -> reqwest::Client {
        let mut rng = rand::rng();

        // Генерация случайного User-Agent
        let user_agent: String = UserAgent().fake();

        // Случайные заголовки
        let accept_languages = [
            "en-US,en;q=0.9",
            "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-GB,en;q=0.9",
            "de-DE,de;q=0.9",
        ];

        let accept_headers = [
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        ];
        // Разные таймауты для разных операций
        let timeout_secs = rng.random_range(10..18); // Общий таймаут: 10-30 сек
        let connect_timeout_secs = rng.random_range(5..10); // Таймаут соединения: 5-10 сек
        let read_timeout_secs = rng.random_range(15..20); // Таймаут чтения: 15-45 сек

        reqwest::Client::builder()
            .user_agent(&user_agent)
            .default_headers({
                let mut headers = reqwest::header::HeaderMap::new();
                headers.insert(
                    "Accept",
                    accept_headers[rng.random_range(0..accept_headers.len())]
                        .parse()
                        .unwrap(),
                );
                headers.insert(
                    "Accept-Language",
                    accept_languages[rng.random_range(0..accept_languages.len())]
                        .parse()
                        .unwrap(),
                );
                headers
            })
            .timeout(std::time::Duration::from_secs(timeout_secs))
            .connect_timeout(std::time::Duration::from_secs(connect_timeout_secs))
            .read_timeout(std::time::Duration::from_secs(read_timeout_secs))
            .build()
            .expect("Failed to build client")
    }

    fn get_page_count(fragment_html: &Html) -> u32 {
        let r = Regex::new(r#""pages_count"\s*:\s*(\d+)"#);
        // Сначала ищем в JavaScript
        if let Ok(selector) = Selector::parse("script") {
            for script in fragment_html.select(&selector) {
                if let Some(text) = script.text().next()
                    && text.contains("window.__DATA__")
                    && let Ok(re) = r.clone()
                    && let Some(caps) = re.captures(text)
                    && let Ok(num) = caps[1].parse::<u32>()
                {
                    return num;
                }
            }
        }

        // Потом ищем в HTML
        Selector::parse(".pages > a:nth-last-of-type(1)")
            .ok()
            .and_then(|selector| fragment_html.select(&selector).next())
            .and_then(|el| el.text().next())
            .and_then(|text| text.trim().parse::<u32>().ok())
            .unwrap_or(1) // Возвращаем 1 вместо 404
    }

    // pub async fn site_date() -> Result<Vec<RanobesData>, reqwest::Error> {
    pub async fn site_date() -> Result<Vec<String>, reqwest::Error> {
        let client = Self::create_client();

        let fragment_html = Self::get_request_and_fragment(&client, &Self::URL.to_string())
            .await
            .expect("not fragment novel");

        let page_count = Self::get_page_count(&fragment_html);

        println!(
            "page count: {}, batch size = {}",
            // Self::PAGE_COUNT,
            page_count,
            Self::BATCH_SIZE
        );

        let mut rng = rand::rng();

        let all_articles = Self::batch_pagination(
            // Self::PAGE_COUNT,
            20,
            // page_count,
            Self::BATCH_SIZE,
            Self::PAGES_URL,
            (1000, 20_000),
            async move |client, url, page_num| match client.get(&url).send().await {
                Ok(resp) => {
                    let body = resp.text().await.unwrap_or_default();
                    let fragment = Html::parse_fragment(&body);

                    let antiflood = Selector::parse(".offpage").expect("antiflood selector");
                    let mut l = fragment.select(&antiflood);
                    if let Some(flood) = l.next() {
                        print!("find captcha: {}", flood.text().next().unwrap_or(""));
                    }

                    let selector = Selector::parse("article.block > div > h2 a").expect("No url");

                    let mut articles = vec![];
                    for el in fragment.select(&selector) {
                        if let Some(href) = el.value().attr("href") {
                            articles.push(href.to_string());
                        }
                    }
                    println!(
                        "page: {}, number: {}, articles: {:#?} ",
                        url, page_num, articles
                    );
                    articles
                }

                Err(e) => {
                    eprintln!("Ошибка на странице {}: {}", page_num, e);
                    vec![]
                }
            },
        )
        .await;

        println!("📋 Всего уникальных ссылок: {}", all_articles.len());
        // println!("all_articles: {:#?}", all_articles);
        Ok(all_articles)
        //     // Дополнительно: случайная задержка перед парсингом деталей
        //     let final_delay = rng.random_range(3000..5000);
        //     println!("⏳ Ожидание {}ms перед парсингом деталей...", final_delay);
        //     tokio::time::sleep(tokio::time::Duration::from_millis(final_delay)).await;

        //     let all_data = Self::batch_urls_parse_novel(
        //         // all_articles[0..=2].to_vec(),
        //         all_articles[0..=5].to_vec(),

        //         Self::BATCH_SIZE as usize,
        //         (1000, 10_000),
        //     )
        //     .await;

        // Ok(all_data)
    }

    pub async fn get_request_and_fragment(
        client: &reqwest::Client,
        url: &String,
    ) -> Result<Html, reqwest::Error> {
        let resp = client.get(url).send().await?;
        let body = resp.text().await?;
        Ok(Html::parse_fragment(&body))
    }

    pub async fn parse_novel(novel: &String) -> Result<RanobesData, reqwest::Error> {
        let client: reqwest::Client = Self::create_client();
        let fragment_html = Self::get_request_and_fragment(&client, novel)
            .await
            .expect("not fragment novel");
        // img of title (path_to_img)
        let mut img: Vec<u8> = Vec::default();

        if let Ok(img_i) = Self::get_image(&fragment_html).await {
            img = img_i
        }

        // name of title(name)
        let title: String = Self::get_title(&fragment_html).await;
        // (total_chapters)
        let total_chapters: i32 = Self::get_total_chapters(&fragment_html).await;

        println!("title: {title}, total chapters: {total_chapters}");

        let chapters_urls = Self::go_to_more_chapters(&fragment_html, &client).await;

        //  (title) and (content)
        let chapters = Self::batch_contents(
            chapters_urls[0..3].to_vec(),
            Self::BATCH_SIZE as usize,
            (5000, 10_000),
        )
        .await; // first el in vec is last chapter of novel
        let hashed_title_image_path = Self::hash_title_and_add_imgs_avif(&title);
        Ok(RanobesData::new(
            img,
            hashed_title_image_path,
            title,
            total_chapters,
            chapters,
        ))
    }

    pub fn hash_title_and_add_imgs_avif(title: &str) -> String {
        use crc32fast::Hasher;
        let mut hasher = Hasher::new();
        hasher.update(title.as_bytes());
        let hash = hasher.finalize();

        format!("imgs/{}.avif", hash)
    }

    pub async fn get_total_chapters(fragment_html: &Html) -> i32 {
        let selectors = vec![
            Selector::parse(".r-fullstory-spec li:nth-child(8) span")
                .expect("title 1 on page get_total_chapters"),
            Selector::parse(".r-fullstory-spec li:nth-child(9) span")
                .expect("title 2 on page get_total_chapters"),
        ];
        let re = Regex::new(r"\d+").unwrap();
        for selector in selectors {
            if let Some(element) = fragment_html.select(&selector).next() {
                let text = element.text().collect::<String>();
                let trimmed = text.trim();

                if !trimmed.is_empty()
                    && trimmed.contains("chapters")
                    && let Some(captures) = re.captures(trimmed)
                    && let Some(matched) = captures.get(0)
                {
                    let chapters: Option<i32> = matched.as_str().trim().parse().ok();
                    match chapters {
                        Some(v) => {
                            println!("✅ Доступных глав: {}", v);
                            return v;
                        }
                        None => {
                            println!("✅ Ошибка поиска глав");
                            continue;
                        }
                    }
                }
            }
        }
        0
    }

    async fn get_chapter_content(url: &String) -> (String, Vec<String>) {
        let client = Self::create_client();
        let fragment_html = Self::get_request_and_fragment(&client, &url.to_string())
            .await
            .expect("request failed");

        let mut paragraphs: Vec<String> = Vec::new();

        // Берем ВСЕ параграфы из #arrticle
        let article_selector = Selector::parse("#arrticle p").expect("Selector error arrticle p");

        for p in fragment_html.select(&article_selector) {
            // Получаем ТОЛЬКО текст, без HTML тегов
            let text: String = p.text().collect();

            let cleaned = text
                .replace(['\n', '\t', '\r'], " ")
                .replace("&nbsp;", " ")
                .replace("&quot;", "\"")
                .replace("&apos;", "'")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .split_whitespace()
                .collect::<Vec<&str>>()
                .join(" ")
                .trim()
                .to_string();

            if !cleaned.is_empty() {
                paragraphs.push(cleaned);
            }
        }

        // Получаем заголовок
        let title = Self::get_title(&fragment_html).await;
        println!(" title = {title}\n paragraphs = {:#?}", paragraphs);
        (title, paragraphs)
        // ("".to_string(),vec![])
    }

    async fn go_to_more_chapters(fragment_html: &Html, client: &reqwest::Client) -> Vec<String> {
        let selector = Selector::parse("a.uppercase:nth-child(3)").expect("error more_chapters");
        let element = fragment_html
            .select(&selector)
            .next()
            .expect("not select more chapters button");
        if let Some(el) = element.value().attr("href") {
            let more_chapters_url = format!("{}{}", Self::DOMAIN, el);
            let more_chapters_page_url = format!("{}{}", more_chapters_url, "page/");

            println!("more chapters = {more_chapters_url}");
            let fragment_html = Self::get_request_and_fragment(client, &more_chapters_url)
                .await
                .expect("not fragment");
            let page_count = Self::get_page_count(&fragment_html);

            let chapters = Self::batch_pagination(
                // Self::PAGE_COUNT,
                1,
                Self::BATCH_SIZE,
                &more_chapters_page_url,
                (1000, 10_000),
                async move |client, url, _| {
                    let fragment_html = Self::get_request_and_fragment(&client, &url)
                        .await
                        .expect("not fragment");

                    let mut chapters = Vec::new();

                    // // Ищем script теги
                    let script_selector = Selector::parse("script").unwrap();

                    for script in fragment_html.select(&script_selector) {
                        let script_text: String = script.text().collect();

                        //     // Ищем window.__DATA__
                        if script_text.contains("window.__DATA__") {
                            // Извлекаем JSON часть
                            if let Some(start) = script_text.find('{')
                                && let Some(end) = script_text.rfind('}')
                            {
                                let json_str = &script_text[start..=end];

                                //                 // Парсим JSON
                                if let Ok(json) = serde_json::from_str::<Value>(json_str)
                                    && let Some(chapters_array) = json.get("chapters")
                                    && let Some(array) = chapters_array.as_array()
                                {
                                    for chapter in array {
                                        if let Some(link) =
                                            chapter.get("link").and_then(|v| v.as_str())
                                        {
                                            chapters.push(link.to_string());
                                        }
                                    }
                                }
                            }
                        }
                    }
                    let len = chapters.len();
                    println!("chapters ({len}) = {chapters:?}\n");
                    chapters
                },
            )
            .await;
            return chapters;
        }
        vec![]
    }

    async fn get_title(fragment_html: &Html) -> String {
        let selectors = vec![
            Selector::parse("h1.title").expect("title on page"),
            Selector::parse("h1.title span").expect("title on page"),
        ];

        for selector in selectors {
            if let Some(element) = fragment_html.select(&selector).next() {
                let mut text = element.text().collect::<String>().trim().to_string();

                // Если это h1 с itemprop="headline", обрезаем текст
                if element.value().name() == "h1"
                    && element.value().attr("itemprop") == Some("headline")
                {
                    let delimiters = ['•', '|'];
                    let mut min_pos = None;
                    for delimiter in delimiters {
                        if let Some(pos) = text.find(delimiter)
                            && min_pos.is_none_or(|current_min| pos < current_min)
                        {
                            min_pos = Some(pos);
                        }
                    }
                    if let Some(pos) = min_pos {
                        text = text[..pos].trim().to_string();
                    }
                }

                if !text.is_empty() {
                    println!("✅ Найден заголовок: '{}'", text);
                    return text;
                }
            }
        }
        "None".to_string()
    }

    async fn get_image(fragment_html: &Html) -> Result<Vec<u8>, Box<dyn Error>> {
        // 1. Находим ссылку на изображение
        let img_selector = Selector::parse(".highslide").expect("image on page");
        let img_url = fragment_html
            .select(&img_selector)
            .next()
            .ok_or("Image not found")?
            .value()
            .attr("href")
            .ok_or("No href attribute")?
            .trim()
            .to_string();

        println!("📸 Найдена ссылка: {}", img_url);

        // 2. Загружаем изображение
        let response = reqwest::get(&img_url).await?;
        let bytes = response.bytes().await?.to_vec();

        println!("✅ Загружено: {} байт", bytes.len());
        // let path = Ranobes::save_as_avif(&bytes.to_vec(), "imgs/a.avif".to_string()).await?;

        Ok(bytes)
    }

    async fn batch_urls_parse_novel(
        urls: Vec<String>,
        batch_size: usize,
        delay_from_to: (u32, u32),
    ) -> Vec<RanobesData> {
        let mut rng = rand::rng();
        let len = urls.len() as u16;
        let mut all_data = vec![];

        for batch_start in (0..=len).step_by(batch_size) {
            let batch_end = (batch_start + batch_size as u16 - 1).min(len);

            println!(
                "🔄 Батч (urls) страниц {}-{} из {}",
                batch_start, batch_end, len
            );
            for i in batch_start..=batch_end {
                if let Some(url) = urls.get(i as usize) {
                    let url = url.to_string();
                    let delay = rng.random_range(delay_from_to.0..delay_from_to.1);
                    tokio::time::sleep(tokio::time::Duration::from_millis(delay as u64)).await;
                    let r_data = Self::parse_novel(&url).await.expect("cant parse chapter");
                    all_data.push(r_data);
                }
            }
        }
        all_data
    }
    pub async fn batch_contents(
        urls: Vec<String>,
        batch_size: usize,
        delay_from_to: (u32, u32),
    ) -> Vec<RanobesChapters> {
        let mut rng = rand::rng();
        let len = urls.len() as u16;
        let mut all_batches = vec![];
        for batch_start in (0..=len).step_by(batch_size) {
            let batch_end = (batch_start + batch_size as u16 - 1).min(len);
            println!(
                "🔄 Батч (urls) страниц {}-{} из {}",
                batch_start, batch_end, len
            );

            let mut one_batch = vec![];
            for i in batch_start..=batch_end {
                if let Some(url) = urls.get(i as usize) {
                    let url = url.to_string();
                    let delay = rng.random_range(delay_from_to.0..delay_from_to.1);
                    tokio::time::sleep(tokio::time::Duration::from_millis(delay as u64)).await;
                    let (title, vec_of_string) = Self::get_chapter_content(&url).await;

                    let compressed_json = Self::compress_chapters(&vec_of_string)
                        .await
                        .expect("failed to compress json");
                    let batch = RanobesChapters::new(title, compressed_json);

                    one_batch.push(batch);
                }
            }
            all_batches.extend(one_batch);
        }
        // println!("all contents = {all_batches:#?}");
        all_batches
    }
    pub async fn compress_chapters(
        strings: &Vec<String>,
    ) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
        // 1. JSON (самый компактная сериализация для текста)
        let json_bytes = serde_json::to_vec(strings)?;
        // 2. Zstd с максимальным уровнем сжатия
        let compressed = zstd::encode_all(json_bytes.as_slice(), 22)?; // Уровень 22 (макс)

        // Статистика (опционально)
        #[cfg(debug_assertions)]
        println!(
            "📦 Сжатие: {} → {} байт ({:.1}x)",
            json_bytes.len(),
            compressed.len(),
            json_bytes.len() as f32 / compressed.len() as f32
        );

        Ok(compressed)
    }
    // /// Распаковка
    // pub async fn decompress_chapters(
    //     data: &[u8],
    // ) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    //     let decompressed = zstd::decode_all(data)?;
    //     let strings: Vec<String> = serde_json::from_slice(&decompressed)?;
    //     Ok(strings)
    // }

    async fn batch_pagination<F, Fut>(
        page_count: u32,
        batch_size: u32,
        local_page_url: &str,
        delay_from_to: (u32, u32),
        process_func: F,
    ) -> Vec<String>
    where
        F: Fn(reqwest::Client, String, u16) -> Fut + Send + Copy + Clone + 'static,
        Fut: Future<Output = Vec<String>> + Send,
    {
        // let page_count = Self::get_page_count(&fragment_html);

        let mut rng = rand::rng();
        let mut all_batches: Vec<String> = vec![];

        for batch_start in (1..=page_count).step_by(batch_size as usize) {
            let batch_end = (batch_start + batch_size - 1).min(page_count);
            println!(
                "🔄 Батч страниц {}-{} из {}",
                batch_start, batch_end, page_count
            );
            // next loop
            let mut tasks: Vec<JoinHandle<Vec<String>>> = vec![];
            for page_num in batch_start..=batch_end {
                let client = Self::create_client();
                let local_page_url = format!("{}{}/", local_page_url, page_num); // Добавил / в конце
                // create tusk
                let delay = rng.random_range(delay_from_to.0..delay_from_to.1);
                let task = tokio::spawn(async move {
                    tokio::time::sleep(tokio::time::Duration::from_millis(delay as u64)).await;

                    process_func(client, local_page_url, page_num as u16).await
                });
                tasks.push(task);
            }
            let results: Vec<Result<Vec<String>, JoinError>> = join_all(tasks).await;
            // Собираем все статьи в один плоский вектор
            let batch_all: Vec<String> = results
                .into_iter()
                .filter_map(|result| result.ok()) // Игнорируем ошибки выполнения задач
                .flatten() // "Расплющиваем" Vec<Vec<String>> в Vec<String>
                .collect();
            println!("batch = {batch_all:?}");
            all_batches.extend(batch_all);
        }

        println!(
            "batch count = {}, batches = {:?}",
            all_batches.len(),
            all_batches
        );
        all_batches
    }
}
