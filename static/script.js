const themeSwitch = document.getElementById('theme-switch');
const themeLabel = document.getElementById('theme-label');
const loader = document.getElementById('loader');

// Theme toggle
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
        themeSwitch.checked = true;
        themeLabel.textContent = 'Light Mode';
    } else {
        document.body.classList.remove('light-theme');
        themeLabel.textContent = 'Dark Mode';
    }
});

themeSwitch.addEventListener('change', () => {
    if (themeSwitch.checked) {
        document.body.classList.add('light-theme');
        themeLabel.textContent = 'Light Mode';
        localStorage.setItem('theme', 'light');
    } else {
        document.body.classList.remove('light-theme');
        themeLabel.textContent = 'Dark Mode';
        localStorage.setItem('theme', 'dark');
    }
});

// File upload and processing
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    loader.style.display = 'block';

    const fileInput = document.getElementById('image-input');
    const resultsDiv = document.getElementById('results');

    if (fileInput.files.length === 0) {
        alert('Please select an image file.');
        loader.style.display = 'none';
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/api/detect', { method: 'POST', body: formData });

        if (!response.ok) {
            resultsDiv.innerHTML = `<p>Error: ${await response.text()}</p>`;
            return;
        }

        const data = await response.json();

        // Show the input image
        const imageElement = document.getElementById('uploaded-image');
        const inputImageURL = URL.createObjectURL(fileInput.files[0]);
        imageElement.src = inputImageURL;

        // Show the output image
        const outputImage = document.getElementById('restored-image');
        outputImage.src = data.output_image;


        // Show the results section
        resultsDiv.style.display = 'block';

    } catch (error) {
        resultsDiv.innerHTML = '<p>An error occurred during processing.</p>';
        console.error(error);
    } finally {
        loader.style.display = 'none';
    }
});
