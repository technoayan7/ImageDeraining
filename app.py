from flask import Flask, render_template, request, send_from_directory, jsonify, url_for
import os
import shutil
import cv2
import torch
import torch.nn.functional as F
from skimage import img_as_ubyte
from runpy import run_path

# Flask app setup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Load Restormer model
task = 'Deraining'
parameters = {
    'inp_channels': 3, 'out_channels': 3, 'dim': 48, 'num_blocks': [4, 6, 6, 8],
    'num_refinement_blocks': 4, 'heads': [1, 2, 4, 8], 'ffn_expansion_factor': 2.66,
    'bias': False, 'LayerNorm_type': 'WithBias', 'dual_pixel_task': False
}
weights = os.path.join('Restormer', 'Deraining', 'pretrained_models', 'deraining.pth')
device = torch.device("cpu")  # Use CPU for inference

# Load model architecture
load_arch = run_path(os.path.join('Restormer', 'basicsr', 'models', 'archs', 'restormer_arch.py'))
model = load_arch['Restormer'](**parameters)
model.load_state_dict(torch.load(weights, map_location=device)['params'])
model.eval()
model.to(device)

def process_image(input_path):
    """Process the input image and return the path to the restored image."""
    img = cv2.cvtColor(cv2.imread(input_path), cv2.COLOR_BGR2RGB)
    input_tensor = torch.from_numpy(img).float().div(255.).permute(2, 0, 1).unsqueeze(0).to(device)

    # Padding for divisibility
    h, w = input_tensor.shape[2:]
    pad_h = (8 - h % 8) % 8
    pad_w = (8 - w % 8) % 8
    input_tensor = F.pad(input_tensor, (0, pad_w, 0, pad_h), mode='reflect')

    # Model inference
    with torch.no_grad():
        restored = model(input_tensor)
        restored = restored[:, :, :h, :w]
        restored = torch.clamp(restored, 0, 1).cpu().permute(0, 2, 3, 1).numpy()
        restored_img = img_as_ubyte(restored[0])

    # Save the output
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], os.path.basename(input_path))
    cv2.imwrite(output_path, cv2.cvtColor(restored_img, cv2.COLOR_RGB2BGR))
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/detect', methods=['POST'])
def detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded file
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_path)

    # Process the image
    try:
        output_path = process_image(input_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Return the paths for input and output images
    return jsonify({
        'input_image': url_for('static', filename=f'uploads/{file.filename}'),
        'output_image': url_for('static', filename=f'results/{os.path.basename(output_path)}')
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
