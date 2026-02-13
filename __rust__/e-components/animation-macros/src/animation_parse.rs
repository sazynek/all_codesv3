mod kw {
    syn::custom_keyword!(and);
    syn::custom_keyword!(is);
    syn::custom_keyword!(on);
}
use std::{collections::HashMap, sync::LazyLock};
use std::fmt;

use proc_macro2::TokenStream;
use quote::ToTokens;
use syn::{
    Error, Ident, Token,
    parse::{Parse, ParseStream, discouraged::Speculative},
};

#[derive(Debug, Clone)]
pub enum AnimationValueComplex {
    Cmd(AnimationCommand),
    Args(AnimationArgs),
    Event(AnimationValue),
}


use std::sync::Mutex;


static STRING_CACHE: LazyLock<Mutex<HashMap<String, &'static str>>> = 
    LazyLock::new(|| Mutex::new(HashMap::new()));

#[derive(Debug, Clone)]
pub enum AnimationValue {
    Int(i32),
    String(String),
    Float(f32),
    Expr(syn::Expr), // Добавляем вариант для выражений
}

impl fmt::Display for AnimationValue {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AnimationValue::Int(s) => write!(f, "{}", s),
            AnimationValue::String(s) => write!(f, "{}", s),
            AnimationValue::Float(s) => write!(f, "{}", s),
            AnimationValue::Expr(s) => write!(f, "{}", s.to_token_stream()),
                    }
    }
}
impl ToTokens for AnimationValue {
    fn to_tokens(&self, tokens: &mut TokenStream) {
        match self {
            AnimationValue::Int(i) => i.to_tokens(tokens),
            AnimationValue::String(s) => s.to_tokens(tokens),
            AnimationValue::Float(f) => f.to_tokens(tokens),
            AnimationValue::Expr(expr) => expr.to_tokens(tokens), // Обрабатываем выражения
        }
    }
}
impl AnimationValue {
    pub fn as_str(&self) -> &'static str {
        match self {
            AnimationValue::String(s) => {
                        // Для строк тоже используем кеш
                        let mut cache = STRING_CACHE.lock().unwrap();
                        *cache.entry(s.clone()).or_insert_with(|| Box::leak(s.clone().into_boxed_str()))
                    },
            AnimationValue::Int(i) => {
                        let string_repr = i.to_string();
                        let mut cache = STRING_CACHE.lock().unwrap();
                        *cache.entry(string_repr.clone()).or_insert_with(|| Box::leak(string_repr.into_boxed_str()))
                    },
            AnimationValue::Float(f) => {
                        let string_repr = f.to_string();
                        let mut cache = STRING_CACHE.lock().unwrap();
                        *cache.entry(string_repr.clone()).or_insert_with(|| Box::leak(string_repr.into_boxed_str()))
                    },
            AnimationValue::Expr(expr) => {
                        let string_repr = expr.to_token_stream().to_string();
                        let mut cache = STRING_CACHE.lock().unwrap();
                        *cache.entry(string_repr.clone()).or_insert_with(|| Box::leak(string_repr.into_boxed_str()))
            },
        }
    }
}


#[derive(Debug, Clone, Default)]
pub struct AnimationMainParser {
    pub params: HashMap<String, AnimationValueComplex>,
}
#[derive(Debug, Clone)]
pub struct AnimationArgs {
    pub key: AnimationValue,
    pub args: AnimationValue,
}

impl Parse for AnimationMainParser {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let mut params = HashMap::new();
        let (e, is_event) = match is_event(input) {
            Ok(s) => (s, true),
            Err(e) => (e.to_string(), false),
        };
        if is_event {
            params.insert(
                format!("event"),
                AnimationValueComplex::Event(AnimationValue::String(e)),
            );
        };

        loop {
            let fork = input.fork();
            if let Ok(cmd) = fork.parse::<AnimationCommand>() {
                input.advance_to(&fork);
                params.insert(
                    format!("cmd_{}_{}", cmd.object, cmd.target),
                    AnimationValueComplex::Cmd(cmd),
                );
            } else {
                let fork = input.fork();
                if let Ok(args) = fork.parse::<AnimationArgs>() {
                    input.advance_to(&fork);
                    params.insert(
                        format!("args_{}", args.key),
                        AnimationValueComplex::Args(args),
                    );
                } else {
                    break;
                }
            }

            if input.parse::<kw::and>().is_err() {
                break;
            }
        }
        // println!("PARAMS {:#?}",params);
        Ok(Self { params })
    }
}

impl Parse for AnimationArgs {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        // println!("AnimationArgs {}",input);
        let key = parse_animation_value(input)?;

        input.parse::<kw::is>()?;
        let value = parse_animation_value(input)?;

        // println!("ARGS {}:{:?}",key,value);
        Ok(AnimationArgs { args: value, key })
    }
}


// Структура для команд (stop button_an on btn0)
#[derive(Debug, Clone)]
pub struct AnimationCommand {
    pub action: AnimationValue, // stop, start
    pub object: AnimationValue, // button_an
    pub target: AnimationValue, // btn0
}
// Парсер для команд (stop button_an on btn0)
impl Parse for AnimationCommand {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        let action = parse_animation_value(input)?; // Команды используют только простые значения

        let object = parse_animation_value(input)?;
        input.parse::<kw::on>()?;
        let target = parse_animation_value(input)?;

        Ok(AnimationCommand {
            action: action,
            object: object,
            target: target,
        })
    }
}

fn parse_animation_value(input: ParseStream) -> Result<AnimationValue, Error> {
    // Парсим как выражение
    let expr: syn::Expr = input.parse()?;
    
    // Преобразуем выражение в AnimationValue, упрощая где возможно
    Ok(simplify_expression(expr))
}

fn simplify_expression(expr: syn::Expr) -> AnimationValue {
    match expr.clone() {
        // Строковые литералы
        syn::Expr::Lit(expr_lit) => {
            match expr_lit.lit {
                syn::Lit::Str(lit_str) => AnimationValue::String(lit_str.value()),
                syn::Lit::Int(lit_int) => {
                    if let Ok(value) = lit_int.base10_parse::<i32>() {
                        AnimationValue::Int(value)
                    } else {
                        AnimationValue::Expr(expr)
                    }
                }
                syn::Lit::Float(lit_float) => {
                    if let Ok(value) = lit_float.base10_parse::<f32>() {
                        AnimationValue::Float(value)
                    } else {
                        AnimationValue::Expr(expr)
                    }
                }
                _ => AnimationValue::Expr(expr),
            }
        }
        // Простые идентификаторы (одиночные)
        syn::Expr::Path(expr_path) => {
            if expr_path.path.segments.len() == 1 && expr_path.path.leading_colon.is_none() {
                let ident = &expr_path.path.segments[0].ident;
                AnimationValue::String(ident.to_string())
            } else {
                AnimationValue::Expr(syn::Expr::Path(expr_path))
            }
        }
        // Вызовы методов и сложные выражения оставляем как есть
        _ => AnimationValue::Expr(expr),
    }
}


fn is_event(input: ParseStream) -> syn::Result<String> {
    if input.peek(Ident) && input.peek2(Token![=>]) {
        let event_ident: Ident = input.parse()?;
        input.parse::<Token![=>]>()?;
        Ok(event_ident.to_string())
    } else {
        Err(syn::Error::new(
            input.span(),
            "Expected event pattern: ident =>",
        ))
    }
}
