Công cụ hỗ trợ cấu hình MLC cho LIS2DUX12
=======================================

Bộ file này hỗ trợ quan sát dữ liệu gia tốc, tính hệ số bộ lọc và tích hợp
cấu hình phân loại đứng yên/đi bộ vào firmware. Tài liệu dành cho người mới
làm quen với quy trình cấu hình Machine Learning Core (MLC).

Các file không tự động tạo thành một chương trình hoàn chỉnh: hai script
Python chạy trên máy tính; file header được dùng trong firmware của MCU.
Chúng không tự huấn luyện cây quyết định hoặc tự chuyển hệ số lọc thành
cấu hình MLC mới.

Danh sách file
--------------

* ``acce_freq.py``: đọc dữ liệu ba trục, tính AccV và vẽ đồ thị thời gian
  cùng phổ biên độ FFT một phía.
* ``filter_calc.py``: tính và in hệ số bộ lọc theo cấu trúc MLC; biểu diễn
  hệ số sau khi chuyển sang float16.
* ``mlc_stationary_walking.h``: bảng 85 lệnh ghi thanh ghi cho cấu hình MLC.
  Theo chú thích trong file, kết quả cây số 1 là ``0 = Stationary`` và
  ``1 = Walking``.

Để hiển thị đồ thị, môi trường Python cần hỗ trợ cửa sổ Matplotlib.
Firmware cần driver giao tiếp với LIS2DUX12 và hàm delay của nền tảng MCU.

1. Quan sát dữ liệu với acce_freq.py
-------------------------------------

Định dạng đầu vào
~~~~~~~~~~~~~~~~

File TXT hoặc CSV chứa đúng ba cột số theo thứ tự X, Y, Z, phân cách bằng
dấu phẩy. Có thể có một dòng tiêu đề đầu tiên và các dòng trống::

    ACC_X [mg],ACC_Y [mg],ACC_Z [mg]
    -155,140,-893
    -172,157,-996
    -164,151,-955
    -167,153,-977

Không thêm cột thời gian hoặc nhãn vào file đầu vào. Đoạn dữ liệu được
chọn phải có ít nhất 4 mẫu; không chứa NaN hoặc giá trị vô hạn.

Đơn vị mặc định là mg, với 1000 mg = 1 g. Script không đổi LSB sang mg,
không resample và không đọc timestamp. Tham số ``--fs`` phải phản ánh tần
số lấy mẫu thực tế của dữ liệu đang đọc.

Cách chạy
~~~~~~~~~

Vẽ toàn bộ bản ghi đã lấy mẫu ở 200 Hz::

    python "acce_freq.py" "data.txt" --fs 200

Chọn đoạn từ 2 giây đến trước 5 giây, hiển thị phổ đến 40 Hz::

    python "acce_freq.py" "data.txt" --fs 200 --start 2 --end 5 --max-freq 40

Đọc dữ liệu được lấy mẫu ở 50 Hz::

    python "acce_freq.py" "data.csv" --fs 50

Xem trợ giúp::

    python "acce_freq.py" --help

Các tham số
~~~~~~~~~~~

.. list-table:: Tham số dòng lệnh
   :header-rows: 1
   :widths: 20 18 62

   * - Tham số
     - Mặc định
     - Chức năng
   * - ``file``
     - Bắt buộc
     - Đường dẫn TXT/CSV.
   * - ``--fs``
     - 200
     - Tần số lấy mẫu thực tế, đơn vị Hz.
   * - ``--start``
     - 0
     - Thời điểm bắt đầu đoạn phân tích, có lấy mẫu tại mốc này nếu có.
   * - ``--end``
     - Cuối file
     - Thời điểm kết thúc, không lấy mẫu tại mốc này.
   * - ``--max-freq``
     - fs/2
     - Giới hạn hiển thị trục tần số; không lọc tín hiệu.
   * - ``--unit``
     - mg
     - Chỉ đổi nhãn đơn vị trên đồ thị, không đổi giá trị dữ liệu.
   * - ``--keep-dc``
     - Tắt
     - Giữ giá trị trung bình khi chuẩn bị tín hiệu cho FFT.
   * - ``--no-show``
     - Tắt
     - Chạy không mở cửa sổ; vẫn tính toán và in thông tin ra terminal.

Script không có tùy chọn ``--save`` và không tự ghi ảnh ra file.

Đọc kết quả
~~~~~~~~~~~

AccV là độ lớn vector gia tốc::

    AccV = sqrt(X^2 + Y^2 + Z^2)

Đồ thị trên hiển thị AccV theo thời gian. Đồ thị dưới hiển thị phổ biên độ
FFT của AccV. Mặc định, script trừ trung bình của đoạn AccV trước khi nhân
cửa sổ Hann và tính FFT. Đồ thị thời gian vẫn giữ nguyên AccV ban đầu.

Với N mẫu và tần số lấy mẫu fs::

    Thời lượng đoạn dữ liệu = N / fs
    Khoảng cách các điểm FFT = fs / N
    Tần số Nyquist = fs / 2

Ví dụ 400 mẫu ở 200 Hz tương ứng 2 giây, khoảng cách điểm FFT 0,5 Hz và
Nyquist 100 Hz. Khoảng cách điểm FFT không đồng nghĩa luôn phân biệt được
hai thành phần tần số gần nhau đến mức đó.

Biên độ phổ được hiệu chỉnh theo cửa sổ Hann, phù hợp để đọc biên độ của
sin ổn định nằm đúng điểm tần số FFT. Với xung va chạm hoặc tín hiệu ngắn,
biên độ phổ không phải gia tốc cực đại của sự kiện. Một đỉnh phổ cũng
không trực tiếp cho biết số lần ngã mỗi giây.

Phổ giúp quan sát thành phần tần số nhưng không tự xác định đâu là nhiễu
hoặc tần số cắt tối ưu. Nên so sánh nhiều bản ghi và kiểm tra ảnh hưởng
của bộ lọc đến kết quả phân loại.

2. Tính hệ số với filter_calc.py
-------------------------------

Script in ``b1``, ``b2``, ``b3``, ``a2``, ``a3`` và ``Gain`` cho cấu trúc::

    H(z) = (b1 + b2*z^-1 + b3*z^-2) / (1 + a2*z^-1 + a3*z^-2)
    y[n] = b1*x[n] + b2*x[n-1] + b3*x[n-2]
           - a2*y[n-1] - a3*y[n-2]
    output[n] = Gain * y[n]

Script chỉ tính hệ số, không lọc file dữ liệu, không vẽ đáp ứng và không
sửa file header cấu hình MLC.

Ví dụ sử dụng
~~~~~~~~~~~~~

Thông thấp bậc 1, MLC ODR 200 Hz, tần số cắt 70 Hz::

    python filter_calc.py --kind low --order 1 --fs 200 --cutoff 70

Thông cao bậc 2, MLC ODR 200 Hz, tần số cắt 5 Hz::

    python filter_calc.py --kind high --order 2 --fs 200 --cutoff 5

Thông dải từ 2 đến 20 Hz, MLC ODR 100 Hz::

    python filter_calc.py --kind band --fs 100 --cutoff 2 20

In hệ số HP cố định::

    python filter_calc.py --kind hp-fixed --fs 200

Xem trợ giúp::

    python filter_calc.py --help

Ý nghĩa tham số
~~~~~~~~~~~~~~

* ``--kind``: ``low`` (LP), ``high`` (HP), ``band`` (BP) hoặc ``hp-fixed``.
  Mặc định là ``high``.
* ``--fs``: MLC ODR tính bằng Hz, mặc định 200. Đây là tốc độ xử lý đầu vào
  của MLC cần dùng khi thiết kế bộ lọc.
* ``--order``: 1 hoặc 2, mặc định 2; chỉ áp dụng cho ``low`` và ``high``.
* ``--cutoff``: một tần số với LP/HP, hai tần số với BP.
  Mặc định LP/HP là 5 Hz, BP là 2 và 20 Hz.

Tần số cắt phải thỏa ``0 < fc < fs/2``; BP cần ``f1 < f2``.
Các ví dụ là hướng dẫn cú pháp, không phải cấu hình tối ưu cho mọi dữ liệu.

Đối với BP, script luôn dùng Butterworth N=1 để tạo bộ lọc thông dải
bậc thực tế là 2. Tham số ``--order`` không thay đổi bậc BP trong script.
Tử số được tách thành ``[1, 0, -1]`` và hệ số Gain.

Với ``hp-fixed``, hệ số cố định là ``b1=0.5``, ``b2=-0.5``, các hệ số còn
lại bằng 0, Gain bằng 1. Script không dùng ``--cutoff`` hoặc ``--order``
trong chế độ này; tần số -3 dB so với độ lợi cực đại là ``fs/4``.

Làm tròn và kiểm tra hệ số
~~~~~~~~~~~~~~~~~~~~~~~~~

Các hệ số được chuyển sang float16 và in dạng thập phân ngắn, không in
bit nhị phân. Script báo lỗi nếu hệ số bị tràn và cảnh báo nếu có cực
nằm trên hoặc ngoài đường tròn đơn vị sau khi làm tròn.

Script cũng cảnh báo khi tần số cắt chuẩn hóa thấp của HP/BP nhỏ hơn
0,02. Không có cảnh báo không đồng nghĩa bộ lọc đã phù hợp với bài toán:
kiểm tra cả đáp ứng lọc và kết quả phân loại trước khi triển khai.

3. Sử dụng mlc_stationary_walking.h
---------------------------------

Header định nghĩa kiểu ``mems_register_t``, macro ``MLC_CONFIG_SIZE`` bằng
85 và mảng ``mlc_stationary_walking_config``. Mỗi phần tử chứa địa chỉ
thanh ghi và một byte dữ liệu cần ghi theo đúng thứ tự xuất từ UCF.

Nạp cấu hình
~~~~~~~~~~~~

1. Khởi tạo giao tiếp I2C và kiểm tra kết nối cảm biến.
2. Ghi lần lượt từng phần tử của mảng, kiểm tra mã trả về mỗi lần ghi.
3. Sau khi ghi thành công phần tử đầu tiên ``{0x13, 0x10}``, chờ 5 ms
   rồi mới ghi phần tử tiếp theo.
4. Sau khi nạp thành công, đọc kết quả MLC bằng driver của dự án và giải
   mã nhãn theo cấu hình.

Khi tích hợp, cung cấp khai báo và định nghĩa hai hàm trên theo nền tảng.

Header hiện định nghĩa trực tiếp mảng ``const``. Trong dự án C, nếu nhiều
file .c cùng include header này có thể phát sinh lỗi định nghĩa trùng khi
liên kết. Cách đơn giản là chỉ include tại file .c thực hiện nạp; cách tổ
chức khác là chuyển định nghĩa mảng sang một file .c và khai báo ``extern``
trong header.

Nhãn đầu ra
~~~~~~~~~~~

Theo chú thích trong header:

* ``0``: Stationary — đứng yên.
* ``1``: Walking — đi bộ.

Nạp cấu hình thành công chỉ xác nhận quá trình ghi không báo lỗi; cần thử
cả hai hoạt động trên thiết bị để kiểm tra kết quả thực tế. Header này
không cung cấp hàm đọc kết quả, xử lý ngắt hoặc in log.

Quy trình thực hành
------------------

1. Thu dữ liệu đúng đơn vị và tần số lấy mẫu, lưu ba cột X/Y/Z.
2. Chạy ``acce_freq.py`` để quan sát AccV và phổ của nhiều bản ghi.
3. Nếu cần bộ lọc tùy chỉnh, chọn cấu hình thử nghiệm rồi chạy
   ``filter_calc.py`` để lấy hệ số.
4. Nhập cấu hình và hệ số phù hợp trong công cụ MLC, trích xuất đặc trưng,
   huấn luyện và đánh giá cây bằng dữ liệu kiểm tra riêng.
5. Khi thay đổi mô hình hoặc bộ lọc, xuất lại UCF và cập nhật bảng cấu hình;
   việc chạy script Python không tự cập nhật header hiện có.
6. Nạp cấu hình vào cảm biến và kiểm tra trên hoạt động thực tế.
