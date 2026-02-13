use super::chapters;
use sea_orm::entity::prelude::*;

#[sea_orm::model]
#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel)]
#[sea_orm(table_name = "novels")]
pub struct Model {
    #[sea_orm(primary_key, auto_increment = true)]
    pub id: i32,
    pub name: String,
    pub path_to_img: String,
    pub total_chapters: i32,

    #[sea_orm(has_many)]
    pub chapters: HasMany<chapters::Entity>,
}

impl ActiveModelBehavior for ActiveModel {}
