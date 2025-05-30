// 写真比較機能用JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // 写真コンテナの取得
  const photoCompareContainers = document.querySelectorAll('.photo-compare-container');
  
  if (photoCompareContainers.length === 0) return;
  
  photoCompareContainers.forEach(function(container) {
    const beforeImgContainer = container.querySelector('.before-photo');
    const afterImgContainer = container.querySelector('.after-photo');
    
    if (!beforeImgContainer || !afterImgContainer) return;
    
    const beforeImg = beforeImgContainer.querySelector('img');
    const afterImg = afterImgContainer.querySelector('img');
    
    if (!beforeImg || !afterImg) return;
    
    // 同期スクロール機能
    beforeImgContainer.addEventListener('scroll', function() {
      afterImgContainer.scrollTop = beforeImgContainer.scrollTop;
      afterImgContainer.scrollLeft = beforeImgContainer.scrollLeft;
    });
    
    afterImgContainer.addEventListener('scroll', function() {
      beforeImgContainer.scrollTop = afterImgContainer.scrollTop;
      beforeImgContainer.scrollLeft = afterImgContainer.scrollLeft;
    });
    
    // 画像ズーム機能
    const zoomInBtn = container.querySelector('.zoom-in');
    const zoomOutBtn = container.querySelector('.zoom-out');
    const resetZoomBtn = container.querySelector('.reset-zoom');
    
    let currentZoom = 100;
    const zoomStep = 10;
    const maxZoom = 200;
    const minZoom = 50;
    
    function updateZoom() {
      beforeImg.style.width = `${currentZoom}%`;
      afterImg.style.width = `${currentZoom}%`;
      
      // ズームレベル表示の更新（存在する場合）
      const zoomLevel = container.querySelector('.zoom-level');
      if (zoomLevel) {
        zoomLevel.textContent = `${currentZoom}%`;
      }
    }
    
    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', function() {
        if (currentZoom < maxZoom) {
          currentZoom += zoomStep;
          updateZoom();
        }
      });
    }
    
    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', function() {
        if (currentZoom > minZoom) {
          currentZoom -= zoomStep;
          updateZoom();
        }
      });
    }
    
    if (resetZoomBtn) {
      resetZoomBtn.addEventListener('click', function() {
        currentZoom = 100;
        updateZoom();
        
        // スクロール位置をリセット
        beforeImgContainer.scrollTop = 0;
        beforeImgContainer.scrollLeft = 0;
      });
    }
    
    // 画像のプリロード
    function preloadImages() {
      if (beforeImg.complete && afterImg.complete) {
        // 両方の画像が読み込み完了したらローディングを非表示
        const loader = container.querySelector('.photo-compare-loader');
        if (loader) {
          loader.style.display = 'none';
        }
        
        // コンテナを表示
        container.classList.add('loaded');
      }
    }
    
    if (beforeImg.complete && afterImg.complete) {
      preloadImages();
    } else {
      beforeImg.onload = preloadImages;
      afterImg.onload = preloadImages;
    }
    
    // 画像比較スライダー機能（オプション）
    const slider = container.querySelector('.comparison-slider');
    if (slider) {
      const beforeContainer = container.querySelector('.before-photo-slider');
      const afterContainer = container.querySelector('.after-photo-slider');
      
      if (beforeContainer && afterContainer) {
        slider.addEventListener('input', function() {
          const sliderValue = slider.value;
          beforeContainer.style.width = `${sliderValue}%`;
        });
      }
    }
    
    // 全画面表示機能
    const fullscreenBtn = container.querySelector('.fullscreen-btn');
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', function() {
        if (container.requestFullscreen) {
          container.requestFullscreen();
        } else if (container.mozRequestFullScreen) { /* Firefox */
          container.mozRequestFullScreen();
        } else if (container.webkitRequestFullscreen) { /* Chrome, Safari and Opera */
          container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) { /* IE/Edge */
          container.msRequestFullscreen();
        }
      });
    }
    
    // 選択モードのサムネイル
    const thumbnails = container.querySelectorAll('.photo-thumbnail');
    thumbnails.forEach(function(thumb) {
      thumb.addEventListener('click', function() {
        const beforeSrc = this.getAttribute('data-before');
        const afterSrc = this.getAttribute('data-after');
        
        if (beforeSrc && afterSrc) {
          // 現在のサムネイルをアクティブにする
          thumbnails.forEach(t => t.classList.remove('active'));
          this.classList.add('active');
          
          // 画像を切り替える
          beforeImg.src = beforeSrc;
          afterImg.src = afterSrc;
          
          // キャプション更新（存在する場合）
          const beforeCaption = container.querySelector('.before-caption');
          const afterCaption = container.querySelector('.after-caption');
          
          if (beforeCaption && this.getAttribute('data-before-caption')) {
            beforeCaption.textContent = this.getAttribute('data-before-caption');
          }
          
          if (afterCaption && this.getAttribute('data-after-caption')) {
            afterCaption.textContent = this.getAttribute('data-after-caption');
          }
        }
      });
    });
  });
}); 