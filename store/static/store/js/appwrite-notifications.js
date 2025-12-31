(function() {
    // Ambil konfigurasi dari variabel global yang di-render oleh Django di base.html
    const { PROJECT_ID, DATABASE_ID, PRODUCT_STOCK_COLLECTION_ID } = APPWRITE_CONFIG;

    if (!PROJECT_ID) {
        console.error('Konfigurasi Appwrite tidak ditemukan di dalam template.');
        return;
    }

    const client = new Appwrite.Client();
    client
        .setEndpoint('https://cloud.appwrite.io/v1')
        .setProject(PROJECT_ID);

    console.log('Appwrite Realtime: Skrip dimuat dan dikonfigurasi.');

    // Fungsi untuk menampilkan notifikasi menggunakan komponen Toast DaisyUI
    function showNotification(message, type = 'info') {
        const notificationElement = document.getElementById('realtime-notification');
        const textElement = document.getElementById('notification-text');
        
        if (!notificationElement || !textElement) return;

        // Atur kelas alert berdasarkan tipe notifikasi
        notificationElement.className = `alert alert-${type} bg-neutral text-neutral-content`;
        textElement.textContent = message;
        notificationElement.classList.remove('hidden');

        // Sembunyikan notifikasi setelah 5 detik
        setTimeout(() => {
            notificationElement.classList.add('hidden');
        }, 5000);
    }

    // Channel yang akan didengarkan
    const channel = `databases.${DATABASE_ID}.collections.${PRODUCT_STOCK_COLLECTION_ID}.documents`;

    // Langganan (Subscribe) ke perubahan di koleksi stok
    client.subscribe(channel, (response) => {
        console.log('Appwrite Realtime: Event diterima!', response);

        const eventType = response.events[0];
        const payload = response.payload;

        // Hanya bereaksi pada event pembuatan atau pembaruan dokumen
        if (eventType.includes('.create') || eventType.includes('.update')) {
            const { product_name, stock_level, product_id } = payload;

            // Logika notifikasi untuk pelanggan
            if (stock_level === 0) {
                showNotification(`Stok untuk "${product_name}" telah habis!`, 'error');
            } else if (stock_level > 0 && stock_level <= 5) {
                showNotification(`Stok "${product_name}" menipis, tersisa ${stock_level} buah!`, 'warning');
            }
            
            // Perbarui UI secara langsung jika pengguna berada di halaman detail produk yang relevan
            updateProductDetailPage(payload);
        }
    });

    function updateProductDetailPage(payload) {
        // Cek apakah pengguna berada di halaman detail produk yang stoknya berubah
        // dengan mencari elemen yang memiliki data-attribute product-id
        const productDetailContainer = document.querySelector(`[data-product-id="${payload.product_id}"]`);
        if (productDetailContainer) {
            const stockElement = productDetailContainer.querySelector('.stock-display');
            if (stockElement) {
                stockElement.textContent = `Stok: ${payload.stock_level}`;
                console.log(`UI diperbarui untuk produk ID ${payload.product_id}`);
            }
        }
    }

    console.log(`Appwrite Realtime: Berlangganan ke channel: ${channel}`);

})();
