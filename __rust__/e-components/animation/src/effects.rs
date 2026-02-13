// effects.rs
use crate::motion::Motion;
use crate::easing::Easing;
use egui::{Color32, Context, Id, Painter, Pos2, Rect, Shape, Ui, UiBuilder, Vec2};

// Базовый трейт для всех эффектов
pub trait Effect {
    fn update(&mut self);
    fn is_finished(&self) -> bool;
    fn start(&mut self);
}

// Ripple эффект как в Material UI
#[derive(Clone)]
pub struct RippleEffect {
    pub position: Pos2,
    pub container_rect: Rect,
    pub radius: Motion<f32>,
    pub alpha: Motion<f32>,
    pub color: Color32,
    started: bool,
}

impl RippleEffect {
    pub fn new(position: Pos2, container_rect: Rect, color: Color32) -> Self {
        let max_radius = Self::calculate_max_radius(position, container_rect);
        let duration = 0.8;
        
        Self {
            position,
            container_rect,
            radius: Motion::new(0.0, max_radius, duration).with_easing(Easing::EaseOut),
            alpha: Motion::new(0.6, 0.0, duration + 0.2)
                .with_easing(Easing::EaseOut)
                .with_delay(0.3),
            color,
            started: false,
        }
    }

    fn calculate_max_radius(center: Pos2, rect: Rect) -> f32 {
        let corners = [
            rect.left_top(),
            rect.right_top(), 
            rect.left_bottom(),
            rect.right_bottom(),
        ];
        
        corners.iter()
            .map(|corner| center.distance(*corner))
            .fold(0.0, |max, dist| max.max(dist))
    }

    pub fn draw(&self, painter: &Painter) {
        if !self.started || self.radius.value() <= 0.0 {
            return;
        }

        let current_radius = self.radius.value();
        let current_alpha = self.alpha.value();

        if current_alpha <= 0.0 {
            return;
        }

        let alpha_byte = (current_alpha * 255.0) as u8;
        let mut ripple_color = self.color;
        ripple_color = Color32::from_rgba_unmultiplied(
            ripple_color.r(),
            ripple_color.g(), 
            ripple_color.b(),
            alpha_byte,
        );

        let circle = Shape::circle_filled(self.position, current_radius, ripple_color);
        painter.with_clip_rect(self.container_rect).add(circle);
    }

    pub fn is_running(&self) -> bool {
        self.started && !self.is_finished()
    }
}

impl Effect for RippleEffect {
    fn update(&mut self) {}
    fn is_finished(&self) -> bool {
        self.started && self.alpha.is_finished()
    }
    fn start(&mut self) {
        self.radius.start();
        self.alpha.start();
        self.started = true;
    }
}

// Bounce эффект
#[derive(Clone)]
pub struct BounceEffect {
    scale: Motion<f32>,
    started: bool,
}

impl BounceEffect {
    pub fn new() -> Self {
        let scale = Motion::new(1.0, 1.1, 0.15).with_easing(Easing::EaseOut);
        Self { scale, started: false }
    }

    pub fn scale(&self) -> f32 {
        if !self.started { 1.0 } else { self.scale.value() }
    }
}

impl Effect for BounceEffect {
    fn update(&mut self) {}
    fn is_finished(&self) -> bool {
        self.started && self.scale.is_finished()
    }
    fn start(&mut self) {
        self.scale.start();
        self.started = true;
    }
}

// Главный менеджер эффектов
#[derive(Clone)]
pub struct AnimationManager {
    ripples: Vec<RippleEffect>,
    bounces: std::collections::HashMap<egui::Id, BounceEffect>,
}

impl AnimationManager {
    pub fn new() -> Self {
        Self {
            ripples: Vec::new(),
            bounces: std::collections::HashMap::new(),
        }
    }

    fn handle_button_click(&mut self, response: &egui::Response, color: Color32) {
        if response.clicked() {
            if let Some(click_pos) = response.interact_pointer_pos() {
                let mut ripple = RippleEffect::new(click_pos, response.rect, color);
                ripple.start();
                self.ripples.push(ripple);
            }

            let mut bounce = BounceEffect::new();
            bounce.start();
            self.bounces.insert(response.id, bounce);
        }
    }

    fn get_button_scale(&self, button_id: egui::Id) -> f32 {
        self.bounces.get(&button_id).map(|bounce| bounce.scale()).unwrap_or(1.0)
    }

    pub fn update(&mut self) {
        self.ripples.retain_mut(|ripple| {
            ripple.update();
            !ripple.is_finished()
        });
        self.bounces.retain(|_, bounce| !bounce.is_finished());
    }

    pub fn draw_ripples(&self, painter: &Painter) {
        for ripple in &self.ripples {
            ripple.draw(painter);
        }
    }
}

// Функция для получения ID менеджера анимаций
fn animation_manager_id() -> Id {
    Id::new("animation_manager")
}

// Глобальный доступ к менеджеру анимаций через контекст
fn get_animation_manager(ctx: &Context) -> AnimationManager {
    ctx.data_mut(|d| d.get_temp(animation_manager_id()))
        .unwrap_or_else(AnimationManager::new)
}

fn set_animation_manager(ctx: &Context, manager: AnimationManager) {
    ctx.data_mut(|d| d.insert_temp(animation_manager_id(), manager));
}

pub fn ripple_button(ui: &mut Ui, text: &str, color: Option<Color32>) -> egui::Response {
    let ctx = ui.ctx().clone();
    
    // Get button ID and current scale BEFORE creating UI
    let button_id = ui.make_persistent_id(text);
    let scale = {
        let manager = get_animation_manager(&ctx);
        manager.get_button_scale(button_id)
    };
    
    // Create button with bounce effect
    let response = if scale != 1.0 {
        let original_rect = ui.available_rect_before_wrap();
        let scaled_rect = Rect::from_center_size(
            original_rect.center(),
            original_rect.size() * scale
        );

   
        let area_response = ui.scope_builder(UiBuilder::new().max_rect(scaled_rect), |ui| {
            ui.button(text)
        });

        area_response.response
    } else {
        ui.button(text)
    };

    // Handle click and add effects
    let ripple_color = color.unwrap_or(Color32::from_rgba_unmultiplied(100, 150, 255, 80));
    let mut manager = get_animation_manager(&ctx);
    manager.handle_button_click(&response, ripple_color);
    
    // Save updated manager
    set_animation_manager(&ctx, manager);
    
    response
}

// Функция для обновления и отрисовки эффектов (вызывается в конце кадра)
pub fn update_and_draw_effects(ctx: &Context) {
    let mut manager = get_animation_manager(ctx);
    manager.update();
    
    let painter = ctx.layer_painter(egui::LayerId::new(
        egui::Order::Foreground, 
        egui::Id::new("ripple_effects")
    ));
    manager.draw_ripples(&painter);
    
    set_animation_manager(ctx, manager);
    ctx.request_repaint();
}
        // ui.allocate_ui_at_rect(scaled_rect, |ui| {
  