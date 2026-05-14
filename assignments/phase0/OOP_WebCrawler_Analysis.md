# Giải thích các tính chất OOP qua dự án WebCrawler

> Phân tích bốn trụ cột Object-Oriented Programming dựa trên codebase thực tế

---

## 1. Giới thiệu

Object-Oriented Programming (OOP) có bốn tính chất cốt lõi: **Abstraction**, **Encapsulation**, **Inheritance**, và **Polymorphism**. Tài liệu này phân tích từng tính chất qua codebase WebCrawler thực tế, chỉ ra chính xác chỗ nào trong code thể hiện tính chất nào, và phân biệt các khái niệm hay bị nhầm lẫn.

---

## 2. Abstraction (Tính trừu tượng)

### 2.1. Định nghĩa

Abstraction là việc **ẩn đi chi tiết triển khai phức tạp** và chỉ phơi ra những gì *cần thiết* cho người dùng. Nó trả lời câu hỏi: *"Cái này làm gì?"* — chứ không phải *"Cái này làm như thế nào?"*

Abstraction thường được cài đặt qua hai cơ chế:

- **Abstract Base Class / Interface** — định nghĩa contract mà subclass phải tuân thủ
- **Public API method** — user chỉ quan tâm đến việc method này làm gì, không cần quan tâm đến logic phức tạp bên trong nó

### 2.2. Minh họa trong code

**Cơ chế 1: Abstract Base Class**

```python
class DeepCrawlStrategy(ABC):
    @abstractmethod
    def crawl(self, start_url, max_depth, max_pages, fetcher) -> list[dict]:
        pass
```

Lớp `DeepCrawlStrategy` định nghĩa *contract*: "bất kỳ chiến lược crawl nào cũng phải implement method `crawl()` với chữ ký này, trả về list các dict". Người dùng chỉ cần biết này này — không cần biết bên trong là BFS, DFS, hay thuật toán nào khác. Decorator `@abstractmethod` ép buộc mọi subclass phải override, và bản thân `DeepCrawlStrategy` không thể được khởi tạo trực tiếp.

**Cơ chế 2: Public API method**

```python
class WebCrawler:
    def run(self, url: str, config: CrawlerRunConfig) -> list[dict]:
        # ... toàn bộ logic phức tạp bên trong
```

Người dùng chỉ cần gọi `crawler.run(url, config)` — không cần biết bên trong có tạo fetcher, lọc domain, hay dispatch sang strategy. Đây là abstraction ở mức *use case*: ẩn workflow phức tạp sau một method đơn.

### 2.3. Tại sao quan trọng

Abstraction giảm tải nhận thức (cognitive load) cho người dùng API và cho phép thay đổi implementation mà không phá vỡ code phía client.

---

## 3. Encapsulation (Tính đóng gói)

### 3.1. Định nghĩa

Encapsulation là việc **gói dữ liệu (state) và các hành vi thao tác trên dữ liệu đó vào cùng một đơn vị (class)**, đồng thời **kiểm soát truy cập** từ bên ngoài. Encapsulation trả lời câu hỏi: *"Ai được phép đụng vào cái gì?"*

Cần phân biệt với abstraction: abstraction là *"ẩn cái gì"*, còn encapsulation là *"bảo vệ state thế nào"*. Hai khái niệm bổ trợ nhau nhưng không đồng nghĩa.

### 3.2. Minh họa trong code

**Ví dụ 1: Gói dữ liệu cấu hình**

```python
class CrawlerRunConfig:
    def __init__(self, deep_crawl_strategy, max_depth=2, max_pages=50,
                 same_domain_only=True, timeout=10.0, headers=None):
        self.deep_crawl_strategy = deep_crawl_strategy
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.timeout = timeout
        self.headers = headers or {"User-Agent": "WebCrawler/1.0"}
```

Đây là ví dụ điển hình về encapsulation: tất cả các thuộc tính cấu hình liên quan đến nhau được *gói* vào một đơn vị duy nhất là `CrawlerRunConfig`. Thay vì truyền 6 tham số rời rạc khắp nơi, ta truyền một config object — dữ liệu đi cùng nhau, dễ quản lý, dễ mở rộng.

**Ví dụ 2: Ẩn implementation detail bằng convention `_`**

```python
class DFSDeepCrawlStrategy(DeepCrawlStrategy):
    def crawl(self, start_url, max_depth, max_pages, fetcher):
        results = []
        visited: set[str] = set()
        self._dfs(start_url, 0, max_depth, max_pages, fetcher, visited, results)
        return results

    def _dfs(self, url, depth, max_depth, max_pages, fetcher, visited, results):
        # logic đệ quy nội bộ
        ...
```

Method `_dfs` với prefix `_` báo hiệu *"đây là chi tiết nội bộ, đừng gọi từ ngoài"*. Public API chỉ là `crawl()`. Lưu ý: Python không có true private — `_` chỉ là convention, nhưng nó là cách Python thực thi encapsulation.

### 3.3. Tại sao quan trọng

Encapsulation ngăn việc state bị thay đổi bừa bãi từ bên ngoài, giúp tracking bug dễ hơn và cho phép refactor nội bộ mà không ảnh hưởng người dùng.

---

## 4. Inheritance (Tính kế thừa)

### 4.1. Định nghĩa

Inheritance cho phép một class **tái sử dụng và mở rộng** từ class khác. Class con (subclass) thừa hưởng interface và/hoặc implementation từ class cha (superclass), tránh lặp code.

### 4.2. Minh họa trong code

```python
class BFSDeepCrawlStrategy(DeepCrawlStrategy):
    def crawl(self, start_url, max_depth, max_pages, fetcher):
        # BFS implementation với deque
        ...

class DFSDeepCrawlStrategy(DeepCrawlStrategy):
    def crawl(self, start_url, max_depth, max_pages, fetcher):
        # DFS implementation với recursion
        ...
```

Cả hai lớp `BFSDeepCrawlStrategy` và `DFSDeepCrawlStrategy` đều kế thừa từ `DeepCrawlStrategy`. Chúng:

- Tái sử dụng *interface* (chữ ký method `crawl`) từ class cha
- Bị ràng buộc phải implement `crawl` (vì class cha đánh dấu nó là `@abstractmethod`)
- Có thể được dùng *thay thế* class cha ở bất cứ đâu mong đợi `DeepCrawlStrategy` (Liskov Substitution Principle)

### 4.3. Tại sao quan trọng

Inheritance tránh duplicate code, tạo phân cấp logic, và là nền tảng để polymorphism hoạt động được.

### 4.4. Lưu ý

Trong assignment này, inheritance được dùng theo kiểu *interface inheritance* — class cha chỉ định nghĩa contract, không có implementation chia sẻ.

---

## 5. Polymorphism (Tính đa hình)

### 5.1. Định nghĩa

Polymorphism là khả năng **một lời gọi method duy nhất tạo ra hành vi khác nhau** tùy theo kiểu thực tế của object. Cần phân biệt hai mức độ:

- **Method overriding** (mức implementation): subclass viết lại method của parent
- **Polymorphism thực sự** (mức usage): code client làm việc qua interface chung mà không cần biết kiểu cụ thể

Method overriding chỉ là *điều kiện cần*. Polymorphism *thực sự* xảy ra khi có client code tận dụng được điều đó.

### 5.2. Minh họa trong code

**Phần "method overriding"** — hai class có cùng method với hành vi khác nhau:

```python
class BFSDeepCrawlStrategy(DeepCrawlStrategy):
    def crawl(self, ...):  # dùng deque, duyệt theo chiều rộng
        ...

class DFSDeepCrawlStrategy(DeepCrawlStrategy):
    def crawl(self, ...):  # dùng đệ quy, duyệt theo chiều sâu
        ...
```

**Phần "polymorphism thực sự"** — nằm ở `WebCrawler.run()`:

```python
class WebCrawler:
    def run(self, url, config):
        ...
        return config.deep_crawl_strategy.crawl(
            start_url=url,
            max_depth=config.max_depth,
            max_pages=config.max_pages,
            fetcher=fetcher,
        )
```

Dòng `config.deep_crawl_strategy.crawl(...)` chính là nơi polymorphism phát huy sức mạnh: `WebCrawler` **không hề biết** strategy cụ thể là BFS hay DFS. Nó chỉ gọi method `crawl()` qua interface chung. Tại runtime, Python tự động dispatch đến đúng implementation dựa trên kiểu thực tế của object.

Kết quả: ta có thể viết:

```python
crawler = WebCrawler()
crawler.run(url, CrawlerRunConfig(deep_crawl_strategy=BFSDeepCrawlStrategy()))
crawler.run(url, CrawlerRunConfig(deep_crawl_strategy=DFSDeepCrawlStrategy()))
```

Không một dòng code nào trong `WebCrawler` cần thay đổi để hỗ trợ chiến lược mới. Thậm chí nếu thêm một strategy mới `RandomCrawlStrategy` cũng không cần đụng tới `WebCrawler`.

### 5.3. Tại sao quan trọng

Polymorphism là chìa khóa để code *mở để mở rộng, đóng để sửa đổi* (Open/Closed Principle).

---

## 6. Tổng kết: Bản đồ OOP trong dự án

| Tính chất | Vị trí trong code | Vai trò |
|---|---|---|
| **Abstraction** | `DeepCrawlStrategy` (ABC), `WebCrawler.run()` | Định nghĩa contract; ẩn workflow |
| **Encapsulation** | `CrawlerRunConfig`, method `_dfs` | Gói dữ liệu cấu hình; ẩn helper nội bộ |
| **Inheritance** | `BFS/DFSDeepCrawlStrategy` kế thừa `DeepCrawlStrategy` | Tái sử dụng interface |
| **Polymorphism** | `config.deep_crawl_strategy.crawl(...)` trong `WebCrawler.run()` | Cho phép thay strategy mà không sửa client |


