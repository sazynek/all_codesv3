use std::sync::Arc;
use std::sync::atomic::{AtomicU32, Ordering};
use std::time::Duration;
use futures::future::{join_all, ok};
use scraper::{Html, Selector};
use reqwest::header;

mod db;
mod macros;
mod models;
mod novelter;

use headless_chrome::{Browser,LaunchOptions};
use std::{thread};
use std::ffi::OsStr;
use rand::Rng;

// #success-text
// .success-circle
// .antibot-btn-success

// T(N) = 180 * sqrt(N / 30)
fn get_delay_for_parsing(rng: &mut impl rand::Rng, num_links: usize) -> u64 {
    const BASE_LINKS: usize = 30;
    const BASE_MAX_MS: u64 = 180_000; // 180 секунд для 30 ссылок
    const MIN_DELAY_MS: u64 = 1_000;  
    
    let ratio = num_links as f64 / BASE_LINKS as f64;
    let multiplier = ratio.sqrt();
    let max_delay_ms = (BASE_MAX_MS as f64 * multiplier) as u64;
    
    rng.random_range(MIN_DELAY_MS..=max_delay_ms)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let all_data = novelter::Ranobes::site_date().await.expect("err site_data"); 
    let all_data:Vec<String> = vec!["https://ranobes.net/".to_string()];

    // let total_links = all_data.len();
    // println!("START TO PARSE ALL");
    
    // // Создаем атомарный счетчик
    // let anti = Arc::new(AtomicU32::new(0));

    // let mut tasks = vec![];
    // let mut rng = rand::rng();
    
    // for url in all_data {
    //     let delay = get_delay_for_parsing(&mut rng, total_links);
    //     println!("URL = {url}, DELAY = {}", delay / 1000);

    //     // Клонируем Arc для каждой задачи
    //     let anti_clone = Arc::clone(&anti);
    //     // ВАЖНО: Явно клонируем String для задачи
    //     let url_clone = url.clone();
        
    //     let task = tokio::spawn(async move {
    //         // Создаем основной клиент для парсинга
    //         let client = novelter::Ranobes::create_client();
    //         tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;

    //         let fragment_html = novelter::Ranobes::get_request_and_fragment(&client, &url_clone)
    //             .await
    //             .expect("not fragment novel");

    //         let antiflood_selector = Selector::parse(".offpage").expect("antiflood selector");
            
    //         let has_captcha = fragment_html.select(&antiflood_selector).next().is_some();
            
    //         if has_captcha {
    //             // Нашли капчу, увеличиваем счетчик
    //             let current = anti_clone.fetch_add(1, Ordering::SeqCst);
    //             println!("🚨 Обнаружена капча! ANTI = {}", current + 1);
                
    //             // === ИЗВЛЕКАЕМ ДАННЫЕ ИЗ HTML ===
    //             // Токен Cloudflare Turnstile
    //             let token_selector = Selector::parse("#cf-chl-widget-xuhap_response").expect("token selector");
    //             println!("FRAGMENT {}",fragment_html.html());
    //             let token = fragment_html
    //                 .select(&token_selector)
    //                 .next()
    //                 .and_then(|input| input.value().attr("value"));
    //             println!("TOKEN {token:?}");
    //             // Проверяем наличие чекбокса "Подтвердите, что вы человек"
    //             let checkbox_label_selector = Selector::parse("span.cb-lb-t").ok();
    //             // let checkbox_input_selector = Selector::parse(".cb-lb > input[type='checkbox']").ok();
    //             let checkbox_input_selector = Selector::parse(".cb-lb > input[type='checkbox']").ok();

                
    //             // Ищем чекбокс
    //             let has_checkbox = checkbox_label_selector.is_some_and(|selector| {
    //                 fragment_html.select(&selector).next().is_some()
    //             });
                
    //             // Ищем input чекбокса
    //             let checkbox_name = checkbox_input_selector.and_then(|selector| {
    //                 fragment_html.select(&selector)
    //                     .next()
    //                     .and_then(|input| input.value().attr("name"))
    //             });
                
    //             println!("Найдены элементы: токен={}, чекбокс={}, имя чекбокса={:?}", 
    //                      token.is_some(), has_checkbox, checkbox_name);
                
    //             match token {
    //                 Some(token) => {
    //                     println!("Найден токен капчи (первые 50 символов): {}...", &token[0..50.min(token.len())]);
                        
    //                     // Создаем НОВЫЙ клиент для запроса капчи
    //                     let captcha_client = reqwest::Client::builder()
    //                         .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    //                         .build()
    //                         .expect("Failed to build client");
                        
    //                     // Подготавливаем данные для POST-запроса
    //                     let mut form_data = vec![
    //                         ("cf-turnstile-response", token),
    //                         ("submit", "I'm not a robot."),
    //                     ];
                        
    //                     // Если есть чекбокс, добавляем его в данные формы
    //                     if let Some(checkbox_name) = checkbox_name {
    //                         // Для чекбокса отправляем значение "on" если он отмечен
    //                         form_data.push((checkbox_name, "on"));
    //                         println!("Добавлен чекбокс '{}' в форму", checkbox_name);
    //                     }
                        
    //                     // Отправляем POST-запрос для "нажатия" на кнопку
    //                     // Используем url_clone
    //                     let response = captcha_client
    //                         .post(&url_clone)
    //                         .header(header::REFERER, &url_clone)
    //                         .form(&form_data)
    //                         .send()
    //                         .await;
                        
    //                     match response {
    //                         Ok(response) => {
    //                             let status = response.status();
    //                             println!("Ответ от сервера после нажатия капчи: статус {}", status);
                                
    //                             match response.text().await {
    //                                 Ok(response_text) => {
    //                                     // Проверяем, прошла ли капча
    //                                     let new_document = Html::parse_document(&response_text);
    //                                     let antiflood_selector = Selector::parse(".offpage").unwrap();
    //                                     let has_antiflood = new_document.select(&antiflood_selector).next().is_some();
                                        
    //                                     if !has_antiflood {
    //                                         println!("✅ Капча успешно пройдена!");
    //                                         // Используем исходный клиент для повторного запроса
    //                                         match client.get(&url_clone).send().await {
    //                                             Ok(second_response) => {
    //                                                 match second_response.text().await {
    //                                                     Ok(new_html) => {
    //                                                         // Теперь можно парсить страницу без капчи
    //                                                         println!("✅ Получена страница после капчи ({} символов)", new_html.len());
    //                                                     }
    //                                                     Err(e) => println!("❌ Ошибка при чтении нового ответа: {}", e),
    //                                                 }
    //                                             }
    //                                             Err(e) => println!("❌ Ошибка при повторном запросе: {}", e),
    //                                         }
    //                                     } else {
    //                                         println!("❌ Капча не пройдена (все еще видим .offpage)");
                                            
    //                                         // Проверяем, не появился ли чекбокс в ответе
    //                                         let checkbox_label_selector = Selector::parse("span.cb-lb-t").ok();
    //                                         let has_checkbox_in_response = checkbox_label_selector.is_some_and(|selector| {
    //                                             new_document.select(&selector).next().is_some()
    //                                         });
                                            
    //                                         if has_checkbox_in_response {
    //                                             println!("⚠️ Возможно нужно отметить чекбокс 'Подтвердите, что вы человек'");
    //                                         }
    //                                     }
    //                                 }
    //                                 Err(e) => {
    //                                     println!("❌ Ошибка при чтении ответа: {}", e);
    //                                 }
    //                             }
    //                         }
    //                         Err(e) => {
    //                             println!("❌ Ошибка при отправке POST-запроса: {}", e);
    //                         }
    //                     }
    //                 }
    //                 None => {
    //                     println!("❌ Токен капчи не найден или не имеет значения");
                        
    //                     // Если нет токена, но есть чекбокс, пробуем отправить только чекбокс
    //                     if let Some(checkbox_name) = checkbox_name {
    //                         println!("⚠️ Пробуем отправить только чекбокс '{}'", checkbox_name);
                            
    //                         let captcha_client = reqwest::Client::builder()
    //                             .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    //                             .build()
    //                             .expect("Failed to build client");
                            
    //                         let form_data = vec![
    //                             (checkbox_name, "on"),
    //                             ("submit", "I'm not a robot."),
    //                         ];
                            
    //                         let response = captcha_client
    //                             .post(&url_clone)
    //                             .header(header::REFERER, &url_clone)
    //                             .form(&form_data)
    //                             .send()
    //                             .await;
                            
    //                         if let Ok(response) = response {
    //                             println!("Ответ от чекбокса: статус {}", response.status());
    //                         }
    //                     }
    //                 }
    //             }
    //         } 
            
    //     });

    //     tasks.push(task);
    // }
    
    // let _ = join_all(tasks).await;
    
    // // Получаем финальное значение
    // let final_anti = anti.load(Ordering::SeqCst);
    // println!("antiflood count = {final_anti}");
    
    Ok(())
}





fn save() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Настройка браузера
    let options = LaunchOptions {
        headless: false, // Видимый браузер
        window_size: Some((1920, 1080)),
        args: vec![
            OsStr::new("--disable-blink-features=AutomationControlled"),
            OsStr::new("--no-sandbox"),
            OsStr::new("--disable-dev-shm-usage"),
            OsStr::new("--disable-web-security"),
            OsStr::new("--disable-features=IsolateOrigins,site-per-process"),
            OsStr::new("--remote-debugging-port=9222"),
            OsStr::new("--user-data-dir=./chrome_profile"),
            OsStr::new("--disable-extensions"),
            OsStr::new("--disable-background-networking"),
            OsStr::new("--disable-sync"),
            OsStr::new("--disable-default-apps"),
            OsStr::new("--disable-translate"),
            OsStr::new("--disable-component-update"),
            OsStr::new("--disable-popup-blocking"),
            OsStr::new("--disable-prompt-on-repost"),
            OsStr::new("--enable-automation"),
            OsStr::new("--start-maximized"),
        ],
        ..Default::default()
    };

    let browser = Browser::new(options)?;
    let tab = browser.new_tab()?;
    
    // 2. Переходим на сайт
    tab.navigate_to("https://ranobes.com")?;
    tab.wait_until_navigated()?;
    thread::sleep(Duration::from_secs(3));
    
    println!("🌐 Страница загружена");
    
    // 3. Попробуем простой клик на кнопку
    if let Ok(button) = tab.find_element("button.antibot-btn-success") {
        println!("✅ Найдена кнопка 'I'm not a robot'");
        button.click()?;
        println!("✅ Кнопка нажата!");
    } else {
        println!("⚠️ Кнопка не найдена, ищем iframe...");
        
        // 4. Если нет кнопки, ищем iframe
        emulate_click_on_iframe(&tab)?;
    }
    
    // 5. Ждем и проверяем результат
    thread::sleep(Duration::from_secs(5));
    
    let content = tab.get_content()?;
    if !content.contains("Antiflood") && !content.contains("cf-turnstile") {
        println!("🎉 УСПЕХ! CloudFlare пройден!");
        
        // Получаем cookies
        let cookies = tab.get_cookies()?;
        for cookie in cookies {
            if cookie.name.contains("cf_clearance") {
                println!("🔑 Получен cf_clearance: {}", cookie.value);
            }
        }
    } else {
        println!("❌ Все еще на странице проверки");
        
        // Сохраняем скриншот для отладки
        match tab.capture_screenshot(
            headless_chrome::protocol::cdp::Page::CaptureScreenshotFormatOption::Png,
            None,
            None,
            true,
        ) {
            Ok(screenshot) => {
                std::fs::write("debug.png", screenshot)?;
                println!("📸 Скриншот сохранен как debug.png");
            }
            Err(e) => println!("⚠️ Не удалось сделать скриншот: {:?}", e),
        }
    }
    
    Ok(())
}
use headless_chrome::browser::tab::point::Point;
// Функция для эмуляции клика на iframe
fn emulate_click_on_iframe(tab: &headless_chrome::Tab) -> Result<(), Box<dyn std::error::Error>> {
    let mut rng = rand::rng();
    
    // Получаем координаты iframe через JavaScript
    let coords = tab.evaluate(
        r#"
        const iframe = document.querySelector('iframe[id^="cf-chl-widget"]');
        if (!iframe) {
            return { error: "No iframe found" };
        }
        
        const rect = iframe.getBoundingClientRect();
        const scrollX = window.pageXOffset || window.scrollX;
        const scrollY = window.pageYOffset || window.scrollY;
        
        return {
            x: Math.floor(rect.left + scrollX),
            y: Math.floor(rect.top + scrollY),
            width: Math.floor(rect.width),
            height: Math.floor(rect.height),
            visible: rect.width > 0 && rect.height > 0
        };
        "#,
        false,
    )?;
    
    if let Some(coords_obj) = coords.value
        && let (Some(x), Some(y), Some(width), Some(height)) = (
            coords_obj.get("x").and_then(|v| v.as_i64()),
            coords_obj.get("y").and_then(|v| v.as_i64()),
            coords_obj.get("width").and_then(|v| v.as_i64()),
            coords_obj.get("height").and_then(|v| v.as_i64()),
        ) {
            println!("🎯 Iframe найден: x={}, y={}, width={}, height={}", x, y, width, height);
            
            // Эмулируем человеческое движение мыши
            println!("🐭 Эмулирую движение мыши...");
            
            // Начинаем с случайной точки
            let start_x = rng.random_range(100..500) as i32;
            let start_y = rng.random_range(100..500) as i32;
            
            // Плавное движение к iframe
            let steps = 20;
            for i in 0..=steps {
                let progress = i as f64 / steps as f64;
                // ease-out cubic
                let ease = 1.0 - (1.0 - progress).powi(3);
                
                let curr_x = (start_x as f64 + (x as f64 - start_x as f64) * ease) as i32;
                let curr_y = (start_y as f64 + (y as f64 - start_y as f64) * ease) as i32;
                
                tab.move_mouse_to_point(Point{x:curr_x as f64,y:  curr_y as f64})?;
                thread::sleep(Duration::from_millis(rng.random_range(20..50)));
            }
            
            // Пауза перед кликом
            thread::sleep(Duration::from_millis(rng.random_range(300..700)));
            
            // Клик в случайной точке внутри iframe (избегаем края)
            let margin = 30;
            let click_x = x as i32 + rng.random_range(margin..width as i32 - margin);
            let click_y = y as i32 + rng.random_range(margin..height as i32 - margin);
            
            println!("🖱️ Кликаю в точку: {}, {}", click_x, click_y);
            
            // Выполняем клик
            tab.click_point(Point { x: click_x as f64,y: click_y as f64 })?;
            
            // Небольшие движения после клика (как у человека)
            for _ in 0..3 {
                let jitter_x = click_x + rng.random_range(-3..3);
                let jitter_y = click_y + rng.random_range(-3..3);
                tab.move_mouse_to_point(Point { x: jitter_x as f64,y: jitter_y as f64 })?;
                thread::sleep(Duration::from_millis(rng.random_range(50..150)));
            }
            
            println!("✅ Клик выполнен!");
            
            return Ok(());
        }
    
    println!("⚠️ Iframe не найден или координаты не получены");
    Ok(())
}