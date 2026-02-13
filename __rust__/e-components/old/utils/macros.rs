#[macro_export]
macro_rules! count_fields {
    () => { 0 };
    ($first:ident $(, $rest:ident)*) => { 1 + $crate::count_fields!($($rest),*) };
}

#[macro_export]
macro_rules! animation_group {
    (
        $struct_name:ident {
            $(
                $field_name:ident : $value:expr
            ),* $(,)?
        }
    ) => {
        paste::paste! {
            const [<NUM_FIELDS_ $struct_name:upper>]: usize = $crate::count_fields!($($field_name),*);
            #[derive(Debug)]
            #[allow(non_camel_case_types)]
            pub struct $struct_name {
                $(
                    $field_name: $crate::AnimationTemplate<f32>,
                    [<get_$field_name>]: f32,
                )*
            }
            
            #[derive(Debug, Default, Clone, Copy)]
            #[allow(non_camel_case_types)]
            pub struct [<$struct_name Values>] {
                $(
                    pub [<get_$field_name>]: f32,
                )*
            }

            impl [<$struct_name Values>] {
                #[inline]
                pub fn unpack(self) -> [f32; [<NUM_FIELDS_ $struct_name:upper>]] {
                    [$(self.[<get_$field_name>]),*]
                }
            }
            
            impl $struct_name {
                #[inline]
                pub fn new() -> Self {
                    let a=Self {
                        $(                        
                            $field_name: $crate::AnimationTemplate::new(
                                $value.0, $value.1, $value.2
                            ).with_easing($value.3),
                            [<get_$field_name>]: $value.0,
                        )*
                    };
                    // println!("--------------------------------------{:?}----------------------------",a);
                    a
                }

                #[inline]
                pub fn handle_interactions(&self, id: &str, interaction: $crate::Interaction) {
                    $(
                        self.$field_name.handle_interaction(id, interaction);
                    )*
                }

                #[inline]
                pub fn animate(&mut self, id: &str) -> [<$struct_name Values>] {
                    $(
                        self.[<get_$field_name>] = self.$field_name.animate(id);
                    )*
                    [<$struct_name Values>] {
                        $([<get_$field_name>]: self.[<get_$field_name>]),*
                    }
                }

                #[inline]
                pub fn start(&self, id: &str) {
                    $(
                        self.$field_name.start(id);
                    )*
                }

                #[inline]
                pub fn stop(&self, id: &str) {
                    $(
                        self.$field_name.stop(id);
                    )*
                }
            }
        }
    };
}

// Макрос anim! для стандартного синтаксиса
#[macro_export]
macro_rules! anim {
    ($start:expr, $end:expr, $duration:expr => $easing:expr) => {
        ($start, $end, $duration, $easing)
    };
}

// Макрос для нескольких групп
#[macro_export]
macro_rules! animation_groups {
    (
        $(
            $struct_name:ident {
                $(
                    $field_name:ident : $value:expr
                ),* $(,)?
            }
        ),* $(,)?
    ) => {
        $(
            $crate::animation_group!($struct_name {
                $($field_name: $value),*
            });
        )*
    };
}



// Универсальный макрос для всех типов кликов
#[macro_export]
macro_rules! click {
    // Базовый случай: любое выражение с clicked() методом + тело + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident $body:block
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        if response.clicked() {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::Toggle);
            $body
        }
        $( $after_block ; )?
        // response
    }};

    // С явным указанием действия [start] + тело + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident [start] $body:block
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        if response.clicked() {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::ClickStart);
            $body
        }
        $( $after_block ; )?
        // response
    }};
    
    // С явным указанием действия [stop] + тело + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident [stop] $body:block
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        if response.clicked() {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::ClickStop);
            $body
        }
        $( $after_block ; )?
        // response
    }};

    // Без тела (пустой блок по умолчанию) + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        $crate::click!($response_expr => ($animation_expr).$id {} $(before => $before_block)? $(after => $after_block)?)
    }};

    // С действием [start] без тела + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident [start]
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        $crate::click!($response_expr => ($animation_expr).$id [start] {} $(before => $before_block)? $(after => $after_block)?)
    }};

    // С действием [stop] без тела + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident [stop]
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        $crate::click!($response_expr => ($animation_expr).$id [stop] {} $(before => $before_block)? $(after => $after_block)?)
    }};

    // С условиями + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident 
        $body:block
        $(aif $aif_condition:expr => $aif_body:block)?
        $(aif aelse $aif_else_condition:expr => $aif_else_body:block)?
        $(aelse => $aelse_body:block)?
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        if response.clicked() {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::Toggle);
            $body
            
            // Обработка условий после основного тела
            $(
                if $aif_condition {
                    $aif_body
                }
            )?
            $(
                else if $aif_else_condition {
                    $aif_else_body
                }
            )?
            $(
                else {
                    $aelse_body
                }
            )?
        }
        $( $after_block ; )?
        // response
    }};
}

// Макрос для hover с before/after
#[macro_export]
macro_rules! hover {
    // Базовый случай: любое выражение с hovered() методом + тело + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident $body:block
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        let is_hovered = response.hovered();
        
        if is_hovered {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverStart);
            $body
        } else {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverEnd);
        }
        $( $after_block ; )?
        response
    }};

    // С телом для обоих состояний: hover start и hover end + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident 
        start $start_body:block
        end $end_body:block
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        let is_hovered = response.hovered();
        
        if is_hovered {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverStart);
            $start_body
        } else {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverEnd);
            $end_body
        }
        $( $after_block ; )?
        response
    }};

    // Без тела (пустой блок по умолчанию) + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident
        $(before =>  $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        $crate::hover!($response_expr => ($animation_expr).$id {} $(before => $before_block)? $(after => $after_block)?)
    }};

    // С условиями для hover start + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident 
        start $start_body:block
        $(aif $aif_condition:expr => $aif_body:block)?
        $(aif aelse $aif_else_condition:expr => $aif_else_body:block)?
        $(aelse => $aelse_body:block)?
        $(before =>  $before_block:block)?
        $(after =>  $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        let is_hovered = response.hovered();
        
        if is_hovered {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverStart);
            $start_body
            
            // Обработка условий после start тела
            $(
                if $aif_condition {
                    $aif_body
                }
            )?
            $(
                else if $aif_else_condition {
                    $aif_else_body
                }
            )?
            $(
                else {
                    $aelse_body
                }
            )?
        } else {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverEnd);
        }
        $( $after_block ; )?
        response
    }};

    // С условиями для обоих состояний + before/after
    (
        $response_expr:expr => ($animation_expr:expr).$id:ident 
        start $start_body:block
        end $end_body:block
        $(aif $aif_condition:expr => $aif_body:block)?
        $(aif aelse $aif_else_condition:expr => $aif_else_body:block)?
        $(aelse => $aelse_body:block)?
        $(before => $before_block:block)?
        $(after => $after_block:block)?
    ) => {{
        let response = $response_expr;
        $( $before_block ; )?
        let is_hovered = response.hovered();
        
        if is_hovered {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverStart);
            $start_body
        } else {
            $animation_expr.handle_interactions(concat!(stringify!($id)), $crate::Interaction::HoverEnd);
            $end_body
        }
        
        // Обработка условий после обоих тел
        $(
            if $aif_condition {
                $aif_body
            }
        )?
        $(
            else if $aif_else_condition {
                $aif_else_body
            }
        )?
        $(
            else {
                $aelse_body
            }
        )?
        
        $( $after_block ; )?
        response
    }};
}

// Псевдоним для обратной совместимости
#[macro_export]
macro_rules! toggle {
    // Просто делегируем click
    ($($tokens:tt)*) => {
        $crate::click!($($tokens)*)
    };
}