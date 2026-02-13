use sea_orm::entity::prelude::*;
// use super::chapters;
use super::novels;

#[sea_orm::model]
#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel)]
#[sea_orm(table_name = "chapters")]
pub struct Model {
    #[sea_orm(primary_key, auto_increment = true)]
    pub id: i32,

    pub title: String, // "Chapter 367: Greatness or mediocrity"

    pub content: Vec<u8>,

    pub novel_id: i32,

    #[sea_orm(belongs_to, from = "novel_id", to = "id")]
    pub novel: HasOne<novels::Entity>,
}

impl ActiveModelBehavior for ActiveModel {}
