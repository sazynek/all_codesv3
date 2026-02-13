mod animation_parse;

use animation_parse::*;
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, visit::Visit, visit_mut::VisitMut,  ItemFn, ItemImpl, ItemStruct};

mod inner_parser;
use inner_parser::*;

use crate::struct_parser::StructInfoCollector;
mod struct_parser;

#[proc_macro_attribute]
pub fn animator_impl(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let mut ast = parse_macro_input!(item as ItemImpl);
    let mut transformer = AnimationTransformer::new(TransformerMode::Impl);
    transformer.visit_item_impl_mut(&mut ast);
    let output = quote! { #ast };
    output.into()
}

#[proc_macro_attribute]
pub fn animator_init(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let mut ast = parse_macro_input!(item as ItemImpl);
    let mut transformer = AnimationTransformer::new(TransformerMode::Init);
    transformer.visit_item_impl_mut(&mut ast);
    let output = quote! { #ast };
    output.into()
}


#[proc_macro_attribute]
pub fn animator_fn(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let mut ast = parse_macro_input!(item as ItemFn);
    let mut transformer = AnimationTransformer::new(TransformerMode::Fn);
    transformer.visit_item_fn_mut(&mut ast);
    let output = quote! {
        #ast
    };
    // println!("\n\nFUNC => {}\n\n", output);

    output.into()
}

#[proc_macro_attribute]
pub fn animator(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemStruct);
    let mut collector = StructInfoCollector::new();
    
    // Используем visit_item_struct для обхода структуры
    collector.visit_item_struct(&input);
    
    match collector.generate_struct_code() {
        Ok(generated_code) => {
            // Для отладки можно вывести сгенерированный код
            // println!("{}", generated_code);
            generated_code.into()
        }
        Err(e) => {
            // Возвращаем ошибку компиляции
            e.into_compile_error().into()
        }
    }
}