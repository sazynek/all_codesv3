/// Анимированная кнопка с автоматическими эффектами
#[macro_export]
macro_rules! animated_button {
    (
        $ui:ident, $text:expr, $anims:ident.$group:ident.$id:ident
    ) => {{
        let response = $ui.button($text);
        let is_hovered = response.hovered();
        let is_clicked = response.clicked();
        
        // Автоматическая обработка всех взаимодействий
        if is_hovered {
            $anims.$group.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverStart);
        } else {
            $anims.$group.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverEnd);
        }
        
        if is_clicked {
            $anims.$group.handle_interactions(concat!(stringify!($id)), $crate::Interaction::Toggle);
        }
        
        response
    }};
}

/// Анимированный слайдер
#[macro_export]
macro_rules! animated_slider {
    (
        $ui:ident, $value:expr, $range:expr, $anims:ident.$group:ident.$id:ident, $text:expr
    ) => {{
        let response = $ui.add(egui::Slider::new($value, $range).text($text));
        let element_id = concat!(stringify!($id));
        
        // Обработка перетаскивания
        if response.dragged() {
            $anims.$group.handle_interactions(element_id, $crate::Interaction::ClickStart);
        }
        
        // Обработка завершения взаимодействия
        if response.drag_stopped() {
            $anims.$group.handle_interactions(element_id, $crate::Interaction::ClickStop);
        }
        
        // Обработка hover - упрощенная версия
        if response.hovered() {
            $anims.$group.handle_interactions(element_id, $crate::Interaction::HoverStart);
        } else {
            $anims.$group.handle_interactions(element_id, $crate::Interaction::HoverEnd);
        }
        
        response
    }};
}