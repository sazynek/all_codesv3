struct Solution {}
impl Solution {
    pub fn remove_duplicates(&self, nums: &mut Vec<i32>) -> i32 {
        let mut length;
        // let mut can_stop = false;
        for _ in 0..nums.len() {
            let current_l = nums.len() as i32;
            println!("{nums:?}");
            for i in 0..nums.len() {
                let one = i;
                let next = i + 1;
                println!("{}", next == nums.len());
                if next >= nums.len() {
                    break;
                }

                if nums[one] == nums[next] {
                    nums.remove(one);
                }
            }
            length = nums.len() as i32;
            println!(
                "length = {}, current_l = {} {length} and {current_l}",
                length, current_l
            );
            if length >= current_l {
                break;
            }
        }
        return nums.len() as i32;
    }
}

pub fn r7() {
    let mut nums = vec![1, 1];
    let sol = Solution {};
    let res = sol.remove_duplicates(&mut nums);
    println!("Result is {res:?}");
}
