use syn::{Field, Ident, ItemStruct, Type, visit::Visit};
use quote::{quote, ToTokens};
use crate::{AnimationMainParser, AnimationValue, AnimationValueComplex};

#[derive(Debug, Clone)]
pub struct FieldInfo {
    pub field_ident: Ident,
    pub ty: Type,
    pub animation_attrs: AnimationMainParser,
    pub value_attr: AnimationMainParser,
}

#[derive(Debug, Clone, Default)]
pub struct StructInfo {
    pub struct_ident: Option<Ident>,
    pub fields: Vec<FieldInfo>,
    pub struct_attrs: AnimationMainParser,
}

pub struct StructInfoCollector {
    pub struct_info: StructInfo,
}

impl<'ast> Visit<'ast> for StructInfoCollector {
    fn visit_item_struct(&mut self, node: &'ast ItemStruct) {
        let mut struct_info = StructInfo {
            struct_ident: Some(node.ident.clone()),
            fields: Vec::new(),
            struct_attrs: AnimationMainParser::default(),
        };

        for attr in &node.attrs {
            if attr.path().is_ident("animation") {
                if let Ok(parsed_args) = attr.parse_args::<AnimationMainParser>() {
                    struct_info.struct_attrs = parsed_args;
                }
            }
        }

        if let syn::Fields::Named(fields_named) = &node.fields {
            for field in &fields_named.named {
                let field_info = self.process_field(field);
                struct_info.fields.push(field_info);
            }
        }

        self.struct_info = struct_info;
        syn::visit::visit_item_struct(self, node);
    }
}

impl StructInfoCollector {
    pub fn new() -> Self {
        Self {
            struct_info: StructInfo::default(),
        }
    }

    fn process_field(&self, field: &Field) -> FieldInfo {
        let field_ident = field.ident.as_ref().expect("No parse field name").clone();
        let mut field_info = FieldInfo {
            field_ident: field_ident.clone(),
            ty: field.ty.clone(),
            animation_attrs: AnimationMainParser::default(),
            value_attr: AnimationMainParser::default(),
        };

        for attr in &field.attrs {
            if attr.path().is_ident("animation") {
                if let Ok(parsed_args) = attr.parse_args::<AnimationMainParser>() {
                    field_info.animation_attrs = parsed_args;
                }
            } else if attr.path().is_ident("value") {
                if let Ok(parsed_args) = attr.parse_args::<AnimationMainParser>() {
                    field_info.value_attr = parsed_args;
                }
            }
        }

        field_info
    }

    pub fn generate_struct_code(&self) -> Result<proc_macro2::TokenStream, syn::Error> {
        let struct_ident = self.struct_info.struct_ident.as_ref()
            .ok_or_else(|| syn::Error::new(
                proc_macro2::Span::call_site(),
                "Struct identifier not found"
            ))?;

        let mut original_fields = Vec::new();
        let mut new_fields = Vec::new();
        let mut update_statements = Vec::new();
        let mut animation_groups = std::collections::HashSet::new();
        let mut group_fields_decl = Vec::new();
        let mut group_fields_init = Vec::new();

        for field in &self.struct_info.fields {
            let field_ident = &field.field_ident;
            let field_type = &field.ty;

            original_fields.push(quote! {
                #field_ident: #field_type
            });

            if !field.animation_attrs.params.is_empty() {
                if let Some(anim_data) = self.extract_animation_data(&field.animation_attrs) {
                    animation_groups.insert(anim_data.group.clone());
                    
                    let group_ident = syn::Ident::new(&anim_data.group, proc_macro2::Span::call_site());
                    let property_ident = syn::Ident::new(&format!("get_{}", anim_data.property), proc_macro2::Span::call_site());
                    
                    // Автоматическое преобразование для element_id
                    let element_id_tokens = self.convert_to_string_literal(&anim_data.element_id);
                    // println!("ELEMENT ID {}",element_id_tokens);
                    update_statements.push(quote! {
                        self.#field_ident = self.#group_ident.animate(#element_id_tokens).#property_ident;
                    });

                    new_fields.push(quote! {
                        #field_ident: #field_type::default()
                    });
                }
            } else if let Some(default_value) = self.extract_default_value(&field.value_attr, field_type) {
                new_fields.push(quote! {
                    #field_ident: #default_value
                });
            } else {
                let init_expr = self.generate_smart_initialization(field_type);
                new_fields.push(quote! {
                    #field_ident: #init_expr
                });
            }
        }

        for group in &animation_groups {
            let group_ident = syn::Ident::new(group, proc_macro2::Span::call_site());
            group_fields_decl.push(quote! {
                #group_ident: #group_ident
            });
            group_fields_init.push(quote! {
                #group_ident: #group_ident::new()
            });
        }
        // println!("UPDATE STATEMENT {}",quote! {#(#update_statements)*});
        let code=quote! {
            // #[derive(Debug)]
            struct #struct_ident {
                #(#original_fields,)*
                #(#group_fields_decl,)*
            }

            impl #struct_ident {
                pub fn new() -> Self {
                    Self {
                        #(#new_fields,)*
                        #(#group_fields_init,)*
                    }
                }

                pub fn update_animations(&mut self) {
                    #(#update_statements)*
                }
            }
        };
        // println!("CODE {}",code);

        Ok(code)
    }

    fn extract_default_value(&self, value_attrs: &AnimationMainParser, field_type: &Type) -> Option<proc_macro2::TokenStream> {
        for (_, value_complex) in &value_attrs.params {
            if let AnimationValueComplex::Args(args) = value_complex {
                if args.key.as_str() == "default" {
                    let default_value = args.args.to_token_stream();
                    let type_str = quote!(#field_type).to_string();
                    
                    return Some(match type_str.as_str() {
                        "String" => {
                            match &args.args {
                                AnimationValue::String(_) => {
                                    // String + строковый литерал → to_string()
                                    quote! { #default_value.to_string() }
                                }
                                _ => {
                                    // Выражение или другое значение - оставляем как есть
                                    default_value
                                }
                            }
                        }
                        "&str" => {
                            match &args.args {
                                AnimationValue::String(_) => {
                                    // &str + строковый литерал → оставляем как есть
                                    default_value
                                }
                                AnimationValue::Expr(_) => {
                                    // &str + выражение, возвращающее String → as_str()
                                    // ВНИМАНИЕ: может вызвать проблемы с временем жизни!
                                    quote! { (#default_value).as_str() }
                                }
                                _ => default_value,
                            }
                        }
                        _ => default_value,
                    });
                }
            }
        }
        None
    }

    // Новая функция для преобразования значений в строковые литералы
    fn convert_to_string_literal(&self, value: &AnimationValue) -> proc_macro2::TokenStream {
        match value {
            AnimationValue::String(s) => {
                // Строковый литерал - оставляем как есть
                quote! { #s }
            }
            AnimationValue::Expr(expr) => {
                // Выражение - используем как есть
                quote! { #expr }
            }
            _ => {
                // Другие типы - преобразуем в строку
                let value_str = value.as_str();
                quote! { #value_str }
            }
        }
    }

    fn extract_animation_data(&self, animation_attrs: &AnimationMainParser) -> Option<FieldAnimationData> {
        let mut group = None;
        let mut property = None;
        let mut element_id = None;

        for (_, value_complex) in &animation_attrs.params {
            if let AnimationValueComplex::Args(args) = value_complex {
                match args.key.as_str() {
                    "group" => {
                        // Поддержка выражений для group
                        group = Some(args.args.clone());
                    }
                    "property" => {
                        // Поддержка выражений для property  
                        property = Some(args.args.clone());
                    }
                    "id" => {
                        // Поддержка выражений для id
                        element_id = Some(args.args.clone());
                    }
                    _ => {}
                }
            }
        }

        if let (Some(group_val), Some(property_val), Some(element_id_val)) = (group, property, element_id) {
            // Преобразуем значения в строки для использования в идентификаторах
            let group_str = match &group_val {
                AnimationValue::String(s) => s.clone(),
                AnimationValue::Expr(expr) => {
                    // Для выражений генерируем уникальное имя на основе токенов
                    let tokens = expr.to_token_stream();
                    format!("expr_{}", quote!(#tokens).to_string().replace(" ", "_"))
                }
                _ => group_val.as_str().to_string(),
            };

            let property_str = match &property_val {
                AnimationValue::String(s) => s.clone(),
                AnimationValue::Expr(expr) => {
                    let tokens = expr.to_token_stream();
                    format!("expr_{}", quote!(#tokens).to_string().replace(" ", "_"))
                }
                _ => property_val.as_str().to_string(),
            };

            Some(FieldAnimationData {
                group: group_str,
                property: property_str,
                element_id: element_id_val,
            })
        } else {
            None
        }
    }

    fn generate_smart_initialization(&self, field_type: &Type) -> proc_macro2::TokenStream {
        let type_str = quote!(#field_type).to_string();

        match type_str.as_str() {
            "f32" | "f64" => quote! { 0.0 },
            "i8" | "i16" | "i32" | "i64" | "i128" | "isize" => quote! { 0 },
            "u8" | "u16" | "u32" | "u64" | "u128" | "usize" => quote! { 0 },
            "bool" => quote! { false },
            "String" => quote! { String::new() },
            "&str" => quote! { "" },
            _ => quote! { #field_type::default() },
        }
    }
}

#[derive(Debug)]
struct FieldAnimationData {
    pub group: String,
    pub property: String,
    pub element_id: AnimationValue,
}