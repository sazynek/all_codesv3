// use std::string::ToString;
struct Solution {}
impl Solution {
    pub fn is_palindrome(&self, x: i128) -> bool {
        let mut strs = x
            .to_string()
            .chars()
            .map(|f| f.to_string())
            .collect::<Vec<String>>();
        let res = recurse(&mut strs);

        return res;
    }
}

pub fn r2() {
    let sol = Solution {};
    let res = sol.is_palindrome(6789012345678900000000098765432109876);
    println!("Result is {res:?}");
}

fn recurse(vec: &mut Vec<String>) -> bool {
    let first = vec.remove(0);

    if vec.len() >= 1 {
        let last = vec.pop().unwrap();
        println!("first: {first}, last: {}", last);
        if last == first && vec.len() != 0 {
            return recurse(vec);
        } else if last == first && vec.len() == 0 {
            return true;
        } else {
            return false;
        }
    }
    println!("vec {vec:?}");
    return true;
}
