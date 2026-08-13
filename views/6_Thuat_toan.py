"""Educational K-Means page; it does not access production clustering state."""

import streamlit as st

from components.kmeans_visual import build_kmeans_education_figure


st.title("Học thuật toán K-Means")
st.caption("K-Means là học không giám sát: không giả định có nhãn lớp đúng sẵn.")

st.header("Các khái niệm nền tảng")
st.markdown(
    """
- **Centroid:** tâm trung bình của các điểm đang thuộc một cụm.
- **Khoảng cách:** K-Means thường dùng khoảng cách Euclid để gán điểm vào tâm gần nhất.
- **Feature scaling:** thuật toán dựa trên khoảng cách nên đặc trưng có thang lớn có thể lấn át đặc trưng khác. Pipeline thật chuẩn hóa R, F, M bằng StandardScaler.
- **Inertia / WCSS:** tổng bình phương khoảng cách trong cụm. Giá trị thấp hơn chỉ thể hiện cụm chặt hơn; không tự động xác định K tốt nhất.
- **Elbow method:** tìm vùng mà việc tăng K chỉ còn cải thiện inertia ít dần.
- **Silhouette:** đánh giá đồng thời độ gắn kết trong cụm và độ tách biệt giữa các cụm.
"""
)

st.header("Lloyd: đúng bốn bước khái niệm")
lloyd_steps = [
    "1. Khởi tạo các centroid.",
    "2. Gán mỗi điểm vào centroid gần nhất.",
    "3. Cập nhật mỗi centroid bằng trung bình các điểm được gán.",
    "4. Lặp việc gán/cập nhật cho đến khi hội tụ hoặc đạt giới hạn dừng.",
]
for item in lloyd_steps:
    st.markdown(item)

step = st.slider("Bước minh họa", min_value=1, max_value=4, value=1)
st.plotly_chart(build_kmeans_education_figure(step), width="stretch")
st.info("Mô phỏng dùng điểm dạy học cố định và không đọc hoặc ghi kết quả mô hình đang hoạt động.")

st.header("K-Means++")
st.write(
    "K-Means++ chọn các tâm ban đầu phân tán có chủ đích để giảm khởi tạo kém. "
    "Đây là chiến lược khởi tạo, không phải một thuật toán phân cụm khác hay bước Lloyd thứ năm."
)

left, right = st.columns(2)
with left:
    st.subheader("Điểm mạnh")
    st.markdown("- Dễ hiểu và triển khai.\n- Nhanh trên dữ liệu số có quy mô phù hợp.\n- Kết quả dễ tóm tắt bằng centroid và hồ sơ cụm.")
with right:
    st.subheader("Hạn chế")
    st.markdown("- Phải chọn K.\n- Nhạy với thang đo và ngoại lệ.\n- Phù hợp hơn với cụm tương đối tròn, kích thước gần nhau.\n- Kết quả phụ thuộc khởi tạo nếu cấu hình không ổn định.")

st.header("Hỏi đáp và diễn giải")
with st.expander("K thấp nhất theo inertia có phải K tốt nhất?"):
    st.write("Không. Inertia luôn không tăng khi thêm cụm; cần kết hợp Elbow, Silhouette và khả năng diễn giải.")
with st.expander("Cluster có phải nhãn đúng của khách hàng?"):
    st.write("Không. Đây là nhóm được khám phá từ RFM, không phải lớp ground-truth.")
with st.expander("Có thể gọi một cụm là “săn sale” chỉ từ RFM?"):
    st.write("Không. Cần dữ liệu khuyến mãi, coupon hoặc giảm giá để kết luận về độ nhạy với sale.")
