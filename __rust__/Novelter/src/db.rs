use futures::future::join_all;
use sea_orm::ConnectionTrait;
use sea_orm::{ActiveModelTrait, EntityTrait, Set};
use sea_orm::{ConnectOptions, Database, DatabaseConnection};
use std::error::Error;
use std::fs;
use tokio::task::JoinHandle;

use crate::create_tables;
use crate::novelter::RanobesChapters;
//novels
use super::models::NovelsActiveModel;
use super::models::NovelsEntity;
// use crate::models::{NovelsModel};

// chapters
use crate::models::ChaptersActiveModel;
use crate::models::ChaptersEntity;
// use crate::models::ChaptersModel;

// test
use sea_orm::{entity::*, query::*};

// pub async fn get_novel_with_chapters(
//     db: &DatabaseConnection,
//     novel_id: i32,
// ) -> Result<(NovelsModel, Vec<ChaptersModel>), sea_orm::DbErr> {
//     let novel =
//         NovelsEntity::find_by_id(novel_id)
//             .one(db)
//             .await?
//             .ok_or(sea_orm::DbErr::RecordNotFound(format!(
//                 "Novel with id {} not found",
//                 novel_id
//             )))?;

//     let chapters = novel.find_related(ChaptersEntity).all(db).await?;

//     Ok((novel, chapters))
// }

pub async fn create_novel_with_chapters_and_load_avif(
    db: &DatabaseConnection,
    novel_data: NovelsActiveModel,
    all_chapters_data: Vec<ChaptersActiveModel>,
    img: &[u8],
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // 1. СОХРАНЯЕМ ИЗОБРАЖЕНИЕ ДО ТРАНЗАКЦИИ
    let img_path = if let ActiveValue::Set(path) = &novel_data.path_to_img {
        path
    } else {
        return Err("Путь к изображению не установлен".into());
    };

    // Сохраняем в AVIF (это может быть долго)
    match save_as_avif(img, img_path).await {
        Ok(_) => {
            // 2. ТОЛЬКО ПОСЛЕ УСПЕШНОГО СОХРАНЕНИЯ - транзакция БД
            let txn = db.begin().await?;

            // 3. Создаем новеллу в транзакции
            let novel_inserted = novel_data.insert(&txn).await?;

            let chapters_with_novel_id: Vec<ChaptersActiveModel> = all_chapters_data
                .into_iter() // берем владение
                .map(|mut chapter| {
                    chapter.novel_id = ActiveValue::Set(novel_inserted.id);
                    chapter
                })
                .collect();

            ChaptersEntity::insert_many(chapters_with_novel_id)
                .exec(&txn)
                .await?;

            // 5. Коммитим транзакцию
            txn.commit().await?;

            println!("✅ Успешно: {}", novel_inserted.name);
            Ok(())
        }
        Err(e) => {
            eprintln!("❌ Ошибка сохранения AVIF: {}", e);
            Err(e)
        }
    }
}

pub async fn convert_data_to_sql_chapters_all_models(
    data: Vec<RanobesChapters>,
) -> Vec<ChaptersActiveModel> {
    let mut tasks: Vec<JoinHandle<ChaptersActiveModel>> = vec![];
    for r_data in data {
        let task: JoinHandle<ChaptersActiveModel> = tokio::spawn(async move {
            ChaptersActiveModel {
                title: Set(r_data.title),
                content: Set(r_data.content),
                // novel_id: Set(novel_id),
                ..Default::default()
            }
        });

        tasks.push(task);
    }
    let vector: Vec<Result<ChaptersActiveModel, tokio::task::JoinError>> = join_all(tasks).await;
    let vector: Vec<ChaptersActiveModel> = vector.into_iter().filter_map(Result::ok).collect();

    vector
}
pub async fn convert_data_to_sql_novel_one_model(
    name: String,
    path_to_img: String,
    total_chapters: i32,
) -> NovelsActiveModel {
    NovelsActiveModel {
        name: Set(name),
        path_to_img: Set(path_to_img),
        total_chapters: Set(total_chapters),
        ..Default::default()
    }
}

async fn save_as_avif(
    bytes: &[u8],
    output_path: &String,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let img = image::load_from_memory(bytes)?;
    println!("🖼  Декодировано: {}x{}", img.width(), img.height());

    img.save_with_format(output_path, image::ImageFormat::Avif)?;

    println!("💾 Сохранено как AVIF: {}", output_path);
    Ok(())
}

pub fn init_img_dir() -> std::io::Result<()> {
    fs::create_dir_all("imgs")?;
    Ok(())
}

pub async fn db_init() -> Result<DatabaseConnection, sea_orm::DbErr> {
    let mut opt = ConnectOptions::new("sqlite://novels.db?mode=rwc".to_owned());
    opt.sqlx_logging(true); // enable SQLx logging
    let db: DatabaseConnection = Database::connect(opt).await?;

    create_tables!(db, NovelsEntity, ChaptersEntity);

    // let pear = NovelsActiveModel {
    //     id: Set(99),
    //     name: Set("Pear name".to_owned()),
    //     path_to_img: Set("Pear path to img".to_owned()),
    //     total_chapters: Set(3),
    // };

    // let pear: NovelsModel = pear.insert(&db).await?;
    // println!("pear = {pear:#?}\n");

    // let item: Option<NovelsModel> = NovelsEntity::find_by_id(99).one(&db).await?;
    // println!("item = {item:#?}\n");

    // Использование
    // let (novel, chapters) = get_novel_with_chapters(&db, 99).await?;
    // println!("{novel:?}, {chapters:#?}");

    // let pear = ChaptersActiveModel{
    //     id: Set(22),
    //     chapter_number: Set(367),
    //     title: Set("Chapter 367: Greatness or mediocrity".to_string()),
    //     content: Set("hallow".to_string()),
    //     novel_id:Set(Some(99)),
    // };

    // let pear: ChaptersModel = pear.insert(&db).await?;

    // println!("pear = {pear:#?}\n");
    // let pear = ChaptersActiveModel{
    //     id: Set(35),
    //     chapter_number: Set(366),
    //     title: Set("Chapter 3676: Greatness".to_string()),
    //     content: Set("wall".to_string()),
    //     novel_id:Set(Some(99)),
    // };

    // let pear: ChaptersModel = pear.insert(&db).await?;
    // println!("pear = {pear:#?}\n");
    // let item: Option<ChapterModel> = ChapterEntity::find_by_id(22).one(&db).await?;
    // println!("item = {item:#?}\n");

    Ok(db)
}
