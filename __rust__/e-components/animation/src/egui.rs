use derive_builder::Builder;
use crate::{easing::Easing, motion::Motion, Animatable};
use egui::{Color32, Vec2};


/// Типы анимируемых свойств
#[derive(Clone, Debug)]
pub enum Property {
    Translation(Vec2),  // Изменяем Position на Translation (относительное смещение)
    Scale(f32),
    Rotation(f32),
    Opacity(f32),
    Color(Color32),
    BackgroundColor(Color32),
    Size(Vec2),
}

impl Animatable for Property {
    fn interpolate(&self, other: &Self, progress: f64) -> Self {
        match (self, other) {
            (Property::Translation(from), Property::Translation(to)) => {
                Property::Translation(from.interpolate(to, progress))
            }
            (Property::Scale(from), Property::Scale(to)) => {
                Property::Scale(from.interpolate(to, progress))
            }
            (Property::Opacity(from), Property::Opacity(to)) => {
                Property::Opacity(from.interpolate(to, progress))
            }
            (Property::Color(from), Property::Color(to)) => {
                Property::Color(from.interpolate(to, progress))
            }
            (Property::BackgroundColor(from), Property::BackgroundColor(to)) => {
                Property::BackgroundColor(from.interpolate(to, progress))
            }
            (Property::Size(from), Property::Size(to)) => {
                Property::Size(from.interpolate(to, progress))
            }
            (Property::Rotation(from), Property::Rotation(to)) => {
                Property::Rotation(from.interpolate(to, progress))
            }
            _ => self.clone(), // fallback
        }
    }
}

/// Спецификация отдельной анимации свойства
#[derive(Builder, Clone,Debug)]
#[builder(setter(into))]
pub struct PropertyAnimation {
    pub property: String,
    pub from: Property,
    pub to: Property,
    #[builder(default = 1.0)]
    pub duration: f64,
    #[builder(default = 0.0)]
    pub delay: f64,
    #[builder(default = Easing::Linear)]
    pub easing: Easing,
    #[builder(default = false)]
    pub repeat: bool,
    #[builder(default = false)]
    pub yoyo: bool,
}

impl PropertyAnimation {
    pub fn builder() -> PropertyAnimationBuilder {
        PropertyAnimationBuilder::default()
    }

    pub fn create_motion(&self) -> Motion<Property> {
        Motion::new(self.from.clone(), self.to.clone(), self.duration)
            .with_delay(self.delay)
            .with_easing(self.easing)
    }
}

/// Состояние анимации
#[derive(Clone, Debug, PartialEq)]
pub enum AnimationState {
    Idle,       // Ожидание
    Running,    // Выполняется
    Paused,     // На паузе
    Finished,   // Завершена
}



/// Основной конструктор анимаций
#[derive(Builder, Clone,Debug)]
#[builder(setter(into, strip_option), pattern = "mutable")]
pub struct Animation {
    #[builder(default = "egui::Id::new(\"animation\")")]
    pub id: egui::Id,
    
    #[builder(default)]
    pub properties: Vec<PropertyAnimation>,
    
    #[builder(default = true)]
    pub auto_start: bool,
    
    #[builder(default = false)]
    pub loop_animation: bool,

    #[builder(default = "AnimationState::Idle")]
    pub initial_state: AnimationState,
}

impl Animation {
    pub fn builder() -> AnimationBuilder {
        AnimationBuilder::default()
    }




   pub fn smooth_jump() -> Animation {
        let jump_up = PropertyAnimation::builder()
            .property("translation".to_string())
            .from(Property::Translation(Vec2::new(0.0, 0.0)))
            .to(Property::Translation(Vec2::new(0.0, -60.0))) // Увеличим высоту прыжка
            .duration(0.6) // Увеличили длительность подъема
            .easing(Easing::EaseOut) // Плавное завершение подъема
            .build()
            .unwrap();

        let jump_down = PropertyAnimation::builder()
            .property("translation".to_string())
            .from(Property::Translation(Vec2::new(0.0, -60.0)))
            .to(Property::Translation(Vec2::new(0.0, 0.0)))
            .duration(0.8) // Увеличили длительность спуска
            .easing(Easing::EaseInOut) // Плавное начало и конец спуска
            .delay(0.6) // Задержка после подъема
            .build()
            .unwrap();

        Animation::builder()
            .id(egui::Id::new("smooth_jump"))
            .properties(vec![jump_up, jump_down])
            .auto_start(true)
            .build()
            .unwrap()
    }


    
}
