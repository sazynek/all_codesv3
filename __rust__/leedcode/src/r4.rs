struct Solution {}
impl Solution {
    pub fn longest_common_prefix(&self, strs: Vec<String>) -> String {
        let mut strs2 = strs
            .iter()
            .map(|i| i.chars().into_iter().rev().collect::<Vec<char>>())
            .collect::<Vec<Vec<char>>>();
        let mut symbol = String::new();
        let mut is_run = true;
        let mut global_prev = String::new();
        while is_run {
            let mut prev = String::from("");
            let mut count = 0;
            // println!("count = {count}; prev = {prev}");
            println!("--------------------------");

            for i in &mut strs2 {
                println!("{i:?}");

                // if i.is_empty() {
                //     if !symbol.is_empty() {
                //         symbol.pop().unwrap();
                //     }
                //     is_run = false;
                //     break;
                // }
                if i.len() > 0 {
                    let first_symbol = i.pop().unwrap();
                    println!("first {first_symbol}");
                    if prev != "" {
                        // println!("prev {prev} == first_symbol {first_symbol}");
                        if prev == first_symbol.to_string() {
                            println!(
                                "used arg {} strLen: {}, counb: {}",
                                count == strs.len() - 1,
                                strs.len() - 1,
                                count
                            );
                            if count == strs.len() - 1 {
                                symbol.push(first_symbol);
                            }
                        } else {
                            println!(
                                "used arg {} strLen: {}, counb: {}",
                                count == strs.len() - 1,
                                strs.len() - 1,
                                count
                            );

                            // if count != 1 {
                            //     symbol.pop();
                            // }
                            is_run = false;
                            break;
                        }
                        prev.clear();
                        prev.push(first_symbol);
                        global_prev.clear();
                        global_prev.push(first_symbol);
                    } else {
                        prev.push(first_symbol);
                        global_prev.push(first_symbol);
                    }

                    // symbol.push();
                    // println!("{i:?}");
                } else {
                    // println!("Else");
                    println!("true {symbol} {}", !i.is_empty());
                    if i.is_empty() && count == 0 && prev == "" && symbol == "" && strs.len() == 1 {
                        println!("global {global_prev} {symbol}");
                        symbol.push_str(&global_prev);
                    }

                    is_run = false;
                    break;
                }
                count += 1;
            }
        }
        println!("{symbol:?}");
        return symbol;
    }
}

pub fn r4() {
    let sol = Solution {};

    // let res = sol.longest_common_prefix(vec![
    //     "prefix".to_string(),
    //     "preface".to_string(),
    //     "preform".to_string(),
    // ]);
    // let res = sol.longest_common_prefix(vec![
    // "flower".to_string(),
    // "flow".to_string(),
    // "flight".to_string(),
    // ]);
    // let res = sol.longest_common_prefix(vec![
    // "international".to_string(),
    // "internet".to_string(),
    // "intermediate".to_string(),
    // ]);
    // let res = sol.longest_common_prefix(vec![
    // "".to_string(),
    // "anything".to_string(),
    // "something".to_string(),
    // ]);
    // let res = sol.longest_common_prefix(vec!["a".to_string(), "a".to_string(), "a".to_string()]);
    // let res = sol.longest_common_prefix(vec![
    // "react".to_string(),
    // "reactnative".to_string(),
    // "reactjs".to_string(),
    // ]);
    // let res = sol.longest_common_prefix(vec![
    //     "university".to_string(),
    //     "uniform".to_string(),
    //     "universe".to_string(),
    // ]);
    let res = sol.longest_common_prefix(vec!["a".to_string()]);
    // let res = sol.longest_common_prefix(vec!["a".to_string(), "a".to_string(), "a".to_string()]);
    // let res =
    // sol.longest_common_prefix(vec!["abab".to_string(), "aba".to_string(), "".to_string()]);

    // ["abab","aba",""]z

    println!("Result: {res}");
}
