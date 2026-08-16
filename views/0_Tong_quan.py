"""Product landing and confidence overview for CustomerInsight AI."""

import streamlit as st
import streamlit.components.v1 as components

from components.states import get_app_state
from components.theme import apply_custom_theme

THREEJS_CONCEPTUAL_VISUAL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: transparent;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  .viz-container {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 380px;
    border-radius: 18px;
    overflow: hidden;
    background: rgba(248, 249, 255, 0.7);
    border: 1px solid #dce9ff;
    background-image: 
      linear-gradient(rgba(53, 37, 205, 0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(53, 37, 205, 0.035) 1px, transparent 1px);
    background-size: 20px 20px;
  }

  #threejs-canvas-host {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
  }

  /* Fallback static display */
  .fallback-viz {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 20px;
    text-align: center;
    gap: 16px;
  }
  .fallback-dots {
    display: flex;
    gap: 24px;
  }
  .fallback-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .fallback-circle {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }

  /* Floating conceptual labels */
  .cluster-label {
    position: absolute;
    opacity: 0;
    transition: opacity 1.2s cubic-bezier(0.16, 1, 0.3, 1), transform 1.2s cubic-bezier(0.16, 1, 0.3, 1);
    transform: translateY(6px);
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(8px);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.02em;
    pointer-events: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }
  .cluster-label.visible {
    opacity: 1;
    transform: translateY(0);
  }
  .label-c1 {
    top: 18%;
    left: 20%;
    color: #3525cd;
    border: 1px solid rgba(53, 37, 205, 0.25);
  }
  .label-c2 {
    top: 42%;
    right: 18%;
    color: #006a61;
    border: 1px solid rgba(0, 106, 97, 0.25);
  }
  .label-c3 {
    bottom: 22%;
    left: 35%;
    color: #8b5cf6;
    border: 1px solid rgba(139, 92, 246, 0.25);
  }

  /* Bottom visual caption */
  .viz-caption {
    position: absolute;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #dce9ff;
    padding: 5px 14px;
    border-radius: 8px;
    font-size: 11px;
    color: #464555;
    white-space: nowrap;
    pointer-events: none;
    box-shadow: 0 2px 6px rgba(53, 37, 205, 0.04);
  }

  @media (prefers-reduced-motion: reduce) {
    .cluster-label {
      transition: none !important;
      opacity: 1 !important;
      transform: none !important;
    }
  }
</style>
</head>
<body>
<div class="viz-container" id="viz-root">
  <div id="threejs-canvas-host"></div>
  
  <div class="cluster-label label-c1" id="lbl-c1">Phân khúc 01</div>
  <div class="cluster-label label-c2" id="lbl-c2">Phân khúc 02</div>
  <div class="cluster-label label-c3" id="lbl-c3">Phân khúc 03</div>
  
  <div class="viz-caption">
    Minh họa trực quan về quá trình hình thành các phân khúc khách hàng.
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r125/three.min.js"></script>
<script>
(function() {
  const container = document.getElementById('threejs-canvas-host');
  const root = document.getElementById('viz-root');
  if (!container || typeof THREE === 'undefined') {
    // Graceful fallback if CDN fails
    renderFallback();
    return;
  }

  function renderFallback() {
    container.innerHTML = `
      <div class="fallback-viz">
        <div class="fallback-dots">
          <div class="fallback-node">
            <div class="fallback-circle" style="background:#3525cd;">01</div>
            <span style="font-size:11px; font-weight:600; color:#3525cd;">Phân khúc 01</span>
          </div>
          <div class="fallback-node">
            <div class="fallback-circle" style="background:#006a61;">02</div>
            <span style="font-size:11px; font-weight:600; color:#006a61;">Phân khúc 02</span>
          </div>
          <div class="fallback-node">
            <div class="fallback-circle" style="background:#8b5cf6;">03</div>
            <span style="font-size:11px; font-weight:600; color:#8b5cf6;">Phân khúc 03</span>
          </div>
        </div>
      </div>
    `;
    const labels = document.querySelectorAll('.cluster-label');
    labels.forEach(l => l.style.display = 'none');
  }

  try {
    const width = root.clientWidth || 460;
    const height = root.clientHeight || 380;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 15;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.appendChild(renderer.domElement);

    // Canonical locked colors:
    // Cluster 01: #3525cd (0x3525cd)
    // Cluster 02: #006a61 (0x006a61)
    // Cluster 03: #8b5cf6 (0x8b5cf6)
    const clusterColors = [
      new THREE.Color(0x3525cd),
      new THREE.Color(0x006a61),
      new THREE.Color(0x8b5cf6)
    ];

    const particleCount = 450;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const initialPositions = new Float32Array(particleCount * 3);
    const targetPositions = new Float32Array(particleCount * 3);
    const colorAttrs = new Float32Array(particleCount * 3);

    const centroids = [
      new THREE.Vector3(-4.0, 2.2, 0),
      new THREE.Vector3(3.8, -0.8, 0),
      new THREE.Vector3(-0.8, -2.8, 0)
    ];

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    for (let i = 0; i < particleCount; i++) {
      const clusterIdx = i % 3;
      const centroid = centroids[clusterIdx];
      const spread = 2.4;

      const tx = centroid.x + (Math.random() - 0.5) * spread;
      const ty = centroid.y + (Math.random() - 0.5) * spread;
      const tz = centroid.z + (Math.random() - 0.5) * (spread * 0.25);

      targetPositions[i * 3] = tx;
      targetPositions[i * 3 + 1] = ty;
      targetPositions[i * 3 + 2] = tz;

      if (prefersReducedMotion) {
        positions[i * 3] = tx;
        positions[i * 3 + 1] = ty;
        positions[i * 3 + 2] = tz;
      } else {
        const x = (Math.random() - 0.5) * 20;
        const y = (Math.random() - 0.5) * 14;
        const z = (Math.random() - 0.5) * 2;
        initialPositions[i * 3] = x;
        initialPositions[i * 3 + 1] = y;
        initialPositions[i * 3 + 2] = z;
        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;
      }

      const color = clusterColors[clusterIdx];
      colorAttrs[i * 3] = color.r;
      colorAttrs[i * 3 + 1] = color.g;
      colorAttrs[i * 3 + 2] = color.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colorAttrs, 3));

    const material = new THREE.PointsMaterial({
      size: 0.15,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // Centroid indicators
    const centroidGroup = new THREE.Group();
    scene.add(centroidGroup);
    centroidGroup.visible = prefersReducedMotion;

    centroids.forEach((pos, i) => {
      const ringGeo = new THREE.RingGeometry(0.3, 0.36, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: clusterColors[i],
        transparent: true,
        opacity: prefersReducedMotion ? 0.6 : 0,
        side: THREE.DoubleSide
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(pos);
      centroidGroup.add(ring);

      const glowGeo = new THREE.SphereGeometry(0.45, 16, 16);
      const glowMat = new THREE.MeshBasicMaterial({
        color: clusterColors[i],
        transparent: true,
        opacity: prefersReducedMotion ? 0.12 : 0
      });
      const glow = new THREE.Mesh(glowGeo, glowMat);
      glow.position.copy(pos);
      centroidGroup.add(glow);
    });

    const startTime = Date.now();
    const scatterDuration = 600;
    const moveDuration = 2200;

    function showLabels() {
      const lbls = document.querySelectorAll('.cluster-label');
      lbls.forEach(l => l.classList.add('visible'));
    }

    if (prefersReducedMotion) {
      showLabels();
      renderer.render(scene, camera);
      return;
    }

    let animationFrameId;
    function animate() {
      animationFrameId = requestAnimationFrame(animate);
      const elapsed = Date.now() - startTime;

      const moveT = Math.min(Math.max((elapsed - scatterDuration) / moveDuration, 0), 1);
      const ease = moveT < 0.5 ? 2 * moveT * moveT : -1 + (4 - 2 * moveT) * moveT;

      const posAttr = geometry.attributes.position;
      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        posAttr.array[i3] = initialPositions[i3] + (targetPositions[i3] - initialPositions[i3]) * ease;
        posAttr.array[i3 + 1] = initialPositions[i3 + 1] + (targetPositions[i3 + 1] - initialPositions[i3 + 1]) * ease;
        posAttr.array[i3 + 2] = initialPositions[i3 + 2] + (targetPositions[i3 + 2] - initialPositions[i3 + 2]) * ease;
      }
      posAttr.needsUpdate = true;

      if (moveT > 0.75) {
        centroidGroup.visible = true;
        centroidGroup.children.forEach(child => {
          const targetOpacity = (child.geometry.type === 'RingGeometry' ? 0.6 : 0.12);
          child.material.opacity = Math.min(child.material.opacity + 0.015, targetOpacity);
        });
      }

      if (moveT >= 1.0) {
        showLabels();
        const pulse = 1 + Math.sin(Date.now() * 0.0025) * 0.03;
        centroidGroup.scale.set(pulse, pulse, pulse);
        points.rotation.y += 0.001;
      }

      renderer.render(scene, camera);
    }

    animate();

    window.addEventListener('resize', () => {
      const w = root.clientWidth || 460;
      const h = root.clientHeight || 380;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });

  } catch (err) {
    renderFallback();
  }
})();
</script>
</body>
</html>
"""


def render_overview() -> None:
    """Render the approved Product Landing and Confidence Overview page."""
    apply_custom_theme()
    state = get_app_state()

    st.title("CustomerInsight AI")

    # --- HERO SECTION ---
    hero_left, hero_right = st.columns([1.1, 0.9], gap="large")

    with hero_left:
        st.markdown(
            """
            <div style="margin-bottom: 12px;">
                <span class="ci-badge">ENTERPRISE ANALYTICS</span>
            </div>
            <h2 style="font-size: 1.85rem; font-weight: 700; line-height: 1.3; color: #0b1c30; margin-bottom: 16px;">
                Biến dữ liệu khách hàng thành những phân khúc có ý nghĩa.
            </h2>
            <p style="font-size: 1.02rem; line-height: 1.6; color: #464555; margin-bottom: 24px;">
                Khám phá cấu trúc khách hàng bằng RFM và K-Means, từ dữ liệu thô đến các phân khúc dễ hiểu, minh bạch và có thể hành động.
            </p>
            """,
            unsafe_allow_html=True,
        )

        cta_col, _ = st.columns([0.5, 0.5])
        with cta_col:
            if st.button("Bắt đầu phân tích →", type="primary", use_container_width=True):
                st.switch_page("views/1_Du_lieu.py")

        st.markdown(
            """
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2dfff;">
                <div class="ci-chip"><span class="ci-chip-dot-teal"></span> RFM Analysis</div>
                <div class="ci-chip"><span class="ci-chip-dot-indigo"></span> K-Means++ Clustering</div>
                <div class="ci-chip"><span class="ci-chip-dot-violet"></span> Customer Profiling</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_right:
        components.html(THREEJS_CONCEPTUAL_VISUAL_HTML, height=390, scrolling=False)

    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

    # --- CAPABILITY STRIP (3 NĂNG LỰC CỐT LÕI) ---
    cap1, cap2, cap3 = st.columns(3, gap="medium")

    with cap1:
        st.markdown(
            """
            <div class="ci-card">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(0, 106, 97, 0.1); color: #006a61; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 16px;">
                    📊
                </div>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 8px;">RFM Analysis</h3>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #464555; margin: 0;">
                    Phân tích mức độ gần đây (Recency), tần suất (Frequency) và giá trị giao dịch (Monetary) để mô tả toàn diện hành vi khách hàng.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cap2:
        st.markdown(
            """
            <div class="ci-card">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(53, 37, 205, 0.1); color: #3525cd; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 16px;">
                    🎯
                </div>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 8px;">K-Means Clustering</h3>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #464555; margin: 0;">
                    Đánh giá khoa học nhiều giá trị K bằng phương pháp Elbow và Silhouette Score để lựa chọn cấu trúc phân cụm tối ưu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cap3:
        st.markdown(
            """
            <div class="ci-card">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(139, 92, 246, 0.1); color: #8b5cf6; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-bottom: 16px;">
                    👤
                </div>
                <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 8px;">Customer Profiling</h3>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #464555; margin: 0;">
                    Hồ sơ hóa đặc trưng RFM từng nhóm, chuyển đổi các cụm thuật toán thành chân dung phân khúc rõ ràng và hữu ích.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 36px;'></div>", unsafe_allow_html=True)

    # --- 5-STEP PHASE 1 JOURNEY ---
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="font-size: 1.5rem; font-weight: 700; color: #0b1c30; margin-bottom: 8px;">
                Quy trình 5 bước chuẩn hóa
            </h2>
            <p style="font-size: 0.95rem; color: #464555; max-width: 650px; margin: 0 auto;">
                Quy trình phân khúc khoa học khép kín từ dữ liệu đầu vào đến kết quả xuất bản.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4, s5 = st.columns(5, gap="small")

    steps_info = [
        ("01", "1", "Dữ liệu", "Nạp dataset mẫu hoặc tải CSV có CustomerID và RFM."),
        ("02", "2", "Khám phá (EDA)", "Imputation trung vị, clipping IQR và chuẩn hóa StandardScaler."),
        ("03", "3", "Chọn K", "Phân tích Elbow & Silhouette để xác nhận số cụm tối ưu."),
        ("04", "4", "Phân cụm", "Chạy K-Means++ deterministic và tính toán hồ sơ cụm."),
        ("05", "5", "Kết quả", "Khám phá phân khúc, tra cứu khách hàng và xuất file CSV."),
    ]

    for col, (big_num, badge_num, title, desc) in zip([s1, s2, s3, s4, s5], steps_info):
        with col:
            st.markdown(
                f"""
                <div class="ci-step-card">
                    <div class="ci-step-number">{big_num}</div>
                    <div class="ci-step-badge">{badge_num}</div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #0b1c30; margin-bottom: 6px;">{title}</div>
                    <div style="font-size: 0.8rem; line-height: 1.45; color: #464555;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 36px;'></div>", unsafe_allow_html=True)

    # --- COMPACT METHOD SUMMARY ---
    st.markdown(
        """
        <div style="background-color: #eff4ff; border: 1px solid #dce9ff; border-radius: 16px; padding: 24px; margin-bottom: 32px;">
            <h3 style="font-size: 1.1rem; font-weight: 600; color: #0b1c30; margin-bottom: 12px;">
                📐 Cơ sở phương pháp luận Phase 1
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; font-size: 0.88rem; color: #464555;">
                <div>• <strong>Định danh:</strong> CustomerID chỉ dùng đối soát, không đưa vào mô hình.</div>
                <div>• <strong>Tiền xử lý:</strong> Median imputation + IQR outlier clipping + StandardScaler.</div>
                <div>• <strong>Thuật toán:</strong> K-Means++ deterministic (random_state=42, n_init=10).</div>
                <div>• <strong>Đánh giá:</strong> Kết hợp WCSS (Elbow) và Silhouette Score để đề xuất K.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- FINAL CTA BANNER ---
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(53,37,205,0.06) 0%, rgba(139,92,246,0.06) 100%); border: 1px solid rgba(53,37,205,0.2); border-radius: 20px; padding: 32px 24px; text-align: center;">
            <h3 style="font-size: 1.35rem; font-weight: 700; color: #0b1c30; margin-bottom: 8px;">
                Sẵn sàng khám phá dữ liệu khách hàng?
            </h3>
            <p style="font-size: 0.95rem; color: #464555; max-width: 500px; margin: 0 auto 20px auto;">
                Bắt đầu quy trình phân tích ngay hôm nay bằng cách nạp dữ liệu hoặc sử dụng bộ dữ liệu mẫu chuẩn.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Bắt đầu ngay →", type="primary", use_container_width=True, key="bottom_cta"):
            st.switch_page("views/1_Du_lieu.py")


render_overview()
