use quote::{ quote, ToTokens};
use syn::{ visit_mut::VisitMut};
use syn::parse::{Parser};
use crate::{AnimationArgs, AnimationCommand, AnimationMainParser, AnimationValueComplex};
use syn::{ImplItem, Ident, FnArg, Pat, Type};

pub struct AnimationTransformer {
    pub mode: TransformerMode,
}

impl AnimationTransformer {
    pub fn new(mode: TransformerMode) -> Self {
        Self { mode }
    }
    
    fn add_init_calls(&self, node: &mut syn::ItemImpl) {
        // Ищем метод update в impl блоке
        let mut update_method = None;
        let mut update_index = None;
        
        for (i, item) in node.items.iter_mut().enumerate() {
            if let ImplItem::Fn(method) = item {
                if method.sig.ident == "update" {
                    update_method = Some(method);
                    update_index = Some(i);
                    break;
                }
            }
        }
        
        if let (Some(method), Some(_index)) = (update_method, update_index) {
            // Находим контекстный аргумент ADD ANIMATION::INIT !!!
            // let ctx_arg = self.find_context_arg(&method.sig.inputs);
            
            // Создаем statements для добавления
            // let init_stmt = if let Some(ctx_ident) = ctx_arg {
            //     syn::parse_quote! {
            //         AnimationContext::init(#ctx_ident);
            //     }
            // } else {
            //     syn::parse_quote! {
            //         compile_error!("Метод update должен содержать аргумент с типом Context");
            //     }
            // };
            
            let update_animations_stmt: syn::Stmt = syn::parse_quote! {
                self.update_animations();
            };
            
            // Добавляем statements в начало блока
            method.block.stmts.insert(0, update_animations_stmt);
            // method.block.stmts.insert(0, init_stmt);
        } else {
            let error_stmt: syn::Stmt = syn::parse_quote! {
                compile_error!("Макрос требует наличия метода update в impl блоке");
            };
            
            let mut error_method: syn::ImplItemFn = syn::parse_quote! {
                fn update(&mut self) {
                    compile_error!("Макрос требует наличия метода update в impl блоке");
                }
            };
            
            error_method.block.stmts.insert(0, error_stmt);
            node.items.insert(0, ImplItem::Fn(error_method));
        }
    }
    
    fn find_context_arg(&self, inputs: &syn::punctuated::Punctuated<FnArg, syn::token::Comma>) -> Option<Ident> {
        for input in inputs {
            if let FnArg::Typed(pat_type) = input {
                if self.is_context_type(&pat_type.ty) {
                    if let Pat::Ident(pat_ident) = &*pat_type.pat {
                        return Some(pat_ident.ident.clone());
                    }
                }
            }
        }
        None
    }
    
    fn is_context_type(&self, ty: &Type) -> bool {
        match ty {
            Type::Reference(type_ref) => self.is_context_type(&type_ref.elem),
            Type::Path(type_path) => {
                if let Some(segment) = type_path.path.segments.last() {
                    segment.ident == "Context"
                } else {
                    false
                }
            }
            _ => false,
        }
    }
}


#[derive(Clone, Copy)]
pub enum TransformerMode {
    Init,    // Добавляет init вызовы + обрабатывает атрибуты when
    Impl,    // Только обрабатывает атрибуты when (старый функционал)
    Fn,    // Только обрабатывает атрибуты when (старый функционал)

}


impl VisitMut for AnimationTransformer {
    fn visit_item_impl_mut(&mut self, node: &mut syn::ItemImpl) {
        // Если режим Init, добавляем init вызовы
        if matches!(self.mode, TransformerMode::Init) {
            self.add_init_calls(node);
        }
        
        // Всегда обрабатываем атрибуты when (общий функционал)
        syn::visit_mut::visit_item_impl_mut(self, node);
    }
    
    // Остальные методы visit_* из вашего существующего AnimationTransformer
    // (обработка блоков, if выражений и т.д.)
    fn visit_block_mut(&mut self, block: &mut syn::Block) {
        let mut new_stmts = Vec::new();

        for stmt in std::mem::take(&mut block.stmts) {
            match stmt {
                syn::Stmt::Expr(expr, semi) => {
                    // Обрабатываем if выражения отдельно
                    if let syn::Expr::If(mut expr_if) = expr {
                        match self.process_if_expression(&mut expr_if) {
                            Ok(()) => {
                                new_stmts.push(syn::Stmt::Expr(syn::Expr::If(expr_if), semi));
                            }
                            Err(e) => {
                                let compile_error = e.into_compile_error();
                                new_stmts.push(syn::Stmt::Expr(syn::Expr::Verbatim(compile_error), semi));
                            }
                        }
                    } else {
                        // Обрабатываем обычные выражения
                        let (animation_attrs, cleaned_expr) = self.extract_animation_attrs(expr);

                        if let Some(animation_attr) = animation_attrs.into_iter().next() {
                            if let Ok(animation_args) = animation_attr.parse_args::<AnimationMainParser>() {
                                let generated_code = self.generate_animation_code(&cleaned_expr, &animation_args);
                                let new_expr: syn::Expr = syn::parse2(generated_code)
                                    .expect("Failed to parse generated code");
                                new_stmts.push(syn::Stmt::Expr(new_expr, semi));
                                continue;
                            }
                        }

                        new_stmts.push(syn::Stmt::Expr(cleaned_expr, semi));
                    }
                }
                _ => new_stmts.push(stmt),
            }
        }

        block.stmts = new_stmts;
        syn::visit_mut::visit_block_mut(self, block);
    }
}



impl AnimationTransformer {
    fn prepend_to_block(&self, block: &mut syn::Block, code: proc_macro2::TokenStream) {
        // Правильно парсим код как последовательность statements внутри блока
        let new_stmts = syn::Block::parse_within
            .parse2(code)
            .expect("Failed to parse generated code into statements");
        
        // Добавляем новые statements в начало блока
        block.stmts.splice(0..0, new_stmts);
    }
fn process_if_expression(&mut self, expr_if: &mut syn::ExprIf) -> Result<(), syn::Error> {
        // Извлекаем атрибуты animation из if выражения
        let mut animation_attrs = Vec::new();
        expr_if.attrs.retain(|attr| {
            if attr.path().is_ident("when") {
                animation_attrs.push(attr.clone());
                false // удаляем атрибут
            } else {
                true
            }
        });

        // Извлекаем событие из условия if
        let condition_event = self.extract_event_from_condition(&expr_if.cond);

        // Обрабатываем найденные атрибуты animation
        for attr in animation_attrs {
            if let Ok(animation_args) = attr.parse_args::<AnimationMainParser>() {
                let attr_event = self.extract_event_name(&animation_args);
                
                // Проверяем соответствие событий
                if !self.events_match(&attr_event, condition_event.as_deref()) {
                    return Err(syn::Error::new_spanned(
                        attr,
                        format!(
                            "Событие '{}' в атрибуте не совпадает с событием '{}' в условии if",
                            attr_event,
                            condition_event.unwrap_or("unknown".to_string())
                        )
                    ));
                }

                let action_code = self.generate_action_code(&animation_args);
                println!("ACTION {}", action_code);
                
                // Добавляем action_code в блок then_branch
                self.prepend_to_block(&mut expr_if.then_branch, action_code);
            }
        }
        
        Ok(())
    }

    fn extract_event_from_condition(&self, cond: &syn::Expr) -> Option<String> {
        // Рекурсивно ищем метод в цепочке вызовов
        match cond {
            syn::Expr::MethodCall(method_call) => {
                // Если это конечный метод в цепочке (например, .clicked())
                Some(method_call.method.to_string())
            }
            syn::Expr::Field(field) => {
                // Если это поле (например, .hovered)
                Some(field.member.to_token_stream().to_string())
            }
            syn::Expr::Group(group) => {
                // Обрабатываем группировку в скобках
                self.extract_event_from_condition(&group.expr)
            }
            syn::Expr::Paren(paren) => {
                // Обрабатываем скобки
                self.extract_event_from_condition(&paren.expr)
            }
            _ => {
                // Пытаемся извлечь из receiver, если это цепочка вызовов
                if let Some(receiver) = self.get_receiver(cond) {
                    self.extract_event_from_condition(receiver)
                } else {
                    None
                }
            }
        }
    }

    fn get_receiver<'a>(&self, expr: &'a syn::Expr) -> Option<&'a syn::Expr> {
        match expr {
            syn::Expr::MethodCall(method_call) => Some(&method_call.receiver),
            syn::Expr::Field(field) => Some(&field.base),
            _ => None,
        }
    }

    fn events_match(&self, attr_event: &str, condition_event: Option<&str>) -> bool {
        match (attr_event, condition_event) {
            ("auto", _) => true, // auto всегда подходит
            (attr, Some(cond)) => attr == cond, // сравниваем если оба есть
            (_, None) => false, // если в условии не нашли событие, а в атрибуте не auto
        }
    }


    fn extract_animation_attrs(&self, mut expr: syn::Expr) -> (Vec<syn::Attribute>, syn::Expr) {
        let attrs = match &mut expr {
            syn::Expr::MethodCall(expr_method) => &mut expr_method.attrs,
            syn::Expr::If(expr_if) => &mut expr_if.attrs,
            _ => return (Vec::new(), expr),
        };

        let mut animation_attrs = Vec::new();
        attrs.retain(|attr| {
            if attr.path().is_ident("when") {
                animation_attrs.push(attr.clone());
                false // удаляем атрибут из исходного выражения
            } else {
                true // сохраняем другие атрибуты
            }
        });

        (animation_attrs, expr)
    }

    fn generate_animation_code(&self, original_expr: &syn::Expr, animation_args: &AnimationMainParser) -> proc_macro2::TokenStream {
        let event_ident = syn::Ident::new(&self.extract_event_name(animation_args), proc_macro2::Span::call_site());

        // Генерируем код для команд и аргументов
        let action_code = self.generate_action_code(animation_args);

        quote! {
            if #original_expr.#event_ident() {
                #action_code
            }
        }
    }

    fn generate_action_code(&self, animation_args: &AnimationMainParser) -> proc_macro2::TokenStream {
        let mut actions = Vec::new();

        for (_, value_complex) in &animation_args.params {
            match value_complex {
                AnimationValueComplex::Cmd(cmd) => {
                    let cmd_code = self.generate_command_code(cmd);
                    actions.push(cmd_code);
                }
                AnimationValueComplex::Args(args) => {
                    let arg_code = self.generate_arg_code(args);
                    actions.push(arg_code);
                }
                AnimationValueComplex::Event(_) => {
                    // Игнорируем событие для if выражений
                    // Условие уже задано в if
                }
            }
        }

        quote! { #(#actions)* }
        // quote! {  }

    }

    fn generate_command_code(&self, cmd: &AnimationCommand) -> proc_macro2::TokenStream {
        let target = &cmd.target;
        let object = syn::Ident::new(&cmd.object.as_str(), proc_macro2::Span::call_site());
        let action = syn::Ident::new(&cmd.action.as_str(), proc_macro2::Span::call_site());

        quote! {
            self.#object.#action(#target);
        }
    }

    fn generate_arg_code(&self, args: &AnimationArgs) -> proc_macro2::TokenStream {
        let var_name = syn::Ident::new(&args.key.as_str(), proc_macro2::Span::call_site());
        let value = &args.args;
        quote! {
            let #var_name = #value;
        }
    }

    fn extract_event_name(&self, animation_args: &AnimationMainParser) -> String {
        for (_, value_complex) in &animation_args.params {
            if let AnimationValueComplex::Event(event_name) = value_complex {
                return event_name.to_string().clone();
            }
        }
        "clicked".to_string()
    }
}


