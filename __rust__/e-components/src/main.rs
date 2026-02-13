fn main() -> eframe::Result {
    // MyApp::new();
    let native_options = eframe::NativeOptions {
        vsync: true, // Включение вертикальной синхронизации для плавной анимации
        ..Default::default()
    };

    eframe::run_native(
        "Плавные прыжки", 
        native_options,
        Box::new(|_cc| Ok(Box::new(MyApp::new()))),
    )
}

use animation::egui::{Animation, Property};
use egui::{Area, Button, Context, CornerRadius, Id, RadioButton, Vec2};
use animation::motion::Motion;

struct MyApp {
    // Храним анимацию прыжка в состоянии приложения
    jump_animation: Animation,
    // Текущее положение кнопки (смещение от начальной позиции)
    current_translation: Vec2,
    // Флаг авто-режима
    auto_mode: bool,
    // Движения для анимации
    jump_up_motion: Motion<Property>,
    jump_down_motion: Motion<Property>,
}

impl MyApp {
    fn new() -> Self {
        // Создаем анимацию прыжка
        let jump_animation = Animation::smooth_jump();
        println!("ANIMATION {:#?}", jump_animation);

        //auto start = ?
        let auto_mode=jump_animation.auto_start;
        // Извлекаем свойства анимации для создания отдельных движений
        let properties = &jump_animation.properties;
        let jump_up_prop = &properties[0];
        let jump_down_prop = &properties[1];
        
        // Создаем движения из свойств анимации
        let jump_up_motion = jump_up_prop.create_motion();
        let jump_down_motion = jump_down_prop.create_motion();
        
        Self { 
            jump_animation,
            current_translation: Vec2::ZERO, // Начальное положение - без смещения
            auto_mode, // Авто-режим включен по умолчанию
            jump_up_motion,
            jump_down_motion,
        }
    }
    
    // Функция для запуска анимации прыжка
    fn start_jump_animation(&mut self) {
        // Сбрасываем и запускаем оба движения
        self.jump_up_motion.start();
        self.jump_down_motion.start();
        println!("Анимация прыжка запущена!");
    }
    
    // Функция обновления анимации
    fn update_animation(&mut self) {
        // Если первое движение (прыжок вверх) еще не завершено
        if !self.jump_up_motion.is_finished() {
            // Получаем текущее значение из движения прыжка вверх
            let value = self.jump_up_motion.value();
            if let Property::Translation(translation) = value {
                self.current_translation = translation;
            }
        } 
        // Если первое движение завершено, но второе (спуск) еще активно
        else if !self.jump_down_motion.is_finished() {
            // Получаем текущее значение из движения спуска
            let value = self.jump_down_motion.value();
            if let Property::Translation(translation) = value {
                self.current_translation = translation;
            }
        }
        // Если оба движения завершены и авто-режим включен - перезапускаем анимацию
        else if self.auto_mode {
            self.start_jump_animation();
        }

    }
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &Context, _frame: &mut eframe::Frame) {
        // Обновляем состояние анимации
        self.update_animation();
        
        egui::CentralPanel::default().show(ctx, |ui| {
            // Отображаем текущее смещение для отладки
            ui.label(format!("Смещение: {:?}", self.current_translation));
            
            // Переключатель авто-режима
            ui.checkbox(&mut self.auto_mode, "Авто-режим");
            
            // Кнопка для ручного запуска анимации
            if ui.add_sized([40.0,20.0],Button::new("Прыжок!")).clicked() {
                self.start_jump_animation();
            }
            
            // Создаем область для кнопки с применением текущего смещения
            let button_rect = ui.available_rect_before_wrap();
            let button_size = Vec2::new(100.0, 50.0);
            
            // Вычисляем позицию кнопки с учетом анимации
            let button_pos = button_rect.center() - button_size /2.0+ self.current_translation;
            
            // Создаем кнопку в вычисленной позиции

            // let button_response = ui.put(
                // egui::Rect::from_min_size(button_pos, button_size),
                // egui::Button::new("Прыгающая кнопка!").corner_radius(CornerRadius::from(7))
            // );
            let button_response = ui.add(egui::Button::new("Прыгающая кнопка!").corner_radius(CornerRadius::from(7)));
            ui.horizontal(|ui|{
                let _ = ui.button("don't move");
            // Обрабатываем клик по кнопке (если не в авто-режиме)
            Area::new(Id::from("hallow")).fixed_pos(button_pos).show(ctx, |ui|{
                if button_response.clicked() && !self.auto_mode {
                    self.start_jump_animation();
                }
                });
            });


        });

        // println!("REPAINT");
        ctx.request_repaint();
        // Запрашиваем перерисовку для плавной анимации
        
    }
}