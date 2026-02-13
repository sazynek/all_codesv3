struct Solution {}
impl Solution {
    pub fn two_sum(&self, nums: Vec<i32>, target: i32) -> Vec<i32> {
        for i in 0..nums.len() {
            for mut j in 0..nums.len() {
                j += 1;
                if j == nums.len() {
                    println!("target is {} + {} = {}", i, j, "break");
                    break;
                }
                let var = nums[i] + nums[j];
                if var == target {
                    println!("target is {} + {} = {}", nums[i], nums[j], var);
                    if i == j {
                        continue;
                    }
                    return vec![i as i32, j as i32];
                }
            }
        }
        return Vec::default();
    }
}

pub fn r1() {
    let sol = Solution {};
    let res = sol.two_sum(vec![2, 5, 5, 11], 10);
    println!("Result is {res:?}");
}
