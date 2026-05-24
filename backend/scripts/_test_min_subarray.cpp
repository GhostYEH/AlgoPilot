#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int target;
    int n;
    if (!(cin >> target >> n)) return 0;
    vector<int> nums(n);
    for (int i = 0; i < n; ++i) cin >> nums[i];
    int left = 0, sum = 0, min_len = n + 1;
    for (int right = 0; right < n; ++right) {
        sum += nums[right];
        while (sum >= target) {
            min_len = min(min_len, right - left + 1);
            sum -= nums[left++];
        }
    }
    if (min_len == n + 1) cout << 0 << "\n";
    else cout << min_len << "\n";
    return 0;
}
