let currentStep = 1;
const totalSteps = 8;
const formData = {};

// ==== Initialisation ====
document.addEventListener('DOMContentLoaded', () => {
    updateProgress();
    updateStepCounter();
});

// ==== Progress functions ====
function updateProgress() {
    const progress = (currentStep / totalSteps) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
}

function updateStepCounter() {
    document.getElementById('currentStep').textContent = currentStep;
    document.getElementById('totalSteps').textContent = totalSteps;
}

function nextStep() {
    if (!validateCurrentStep()) return;

    saveCurrentStepData();

    if (currentStep < totalSteps) {
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('active');
        currentStep++;
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('active');
        updateProgress();
        updateStepCounter();

        if (currentStep === totalSteps) showSummary();
    }
}

function prevStep() {
    if (currentStep > 1) {
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('active');
        currentStep--;
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('active');
        updateProgress();
        updateStepCounter();
    }
}

// ==== Validation ====
function validateCurrentStep() {
    const currentStepElement = document.querySelector(`.step[data-step="${currentStep}"]`);
    const requiredInputs = currentStepElement.querySelectorAll('input[required], select[required]');
    for (let input of requiredInputs) {
        if (!input.value) {
            alert('Please complete all required fields');
            return false;
        }
    }

    const hiddenInputs = currentStepElement.querySelectorAll('input[type="hidden"]');
    for (let input of hiddenInputs) {
        if (input.hasAttribute('required') && !input.value) {
            alert('Please select an option');
            return false;
        }
    }
    return true;
}

// ==== Save step data ====
function saveCurrentStepData() {
    const currentStepElement = document.querySelector(`.step[data-step="${currentStep}"]`);
    const inputs = currentStepElement.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (input.type === 'checkbox') {
            if (input.checked) formData[input.name] = input.value;
        } else if (input.type !== 'file') {
            formData[input.name] = input.value;
        }
    });
}

// ==== Option selection ====
function selectOption(element, fieldName, value) {
    const parent = element.parentElement;
    parent.querySelectorAll('.option-card').forEach(card => card.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById(fieldName).value = value;
    formData[fieldName] = value;
}

// ==== Photo preview ====
function previewPhoto(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('photoPreview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ==== Camera ====
function openCamera() {
    const modal = document.createElement('div');
    modal.id = 'cameraModal';
    modal.style = `
        position: fixed; top:0; left:0; width:100%; height:100%;
        background: rgba(0,0,0,0.85); display:flex; justify-content:center; align-items:center; flex-direction:column;
        z-index: 9999;
    `;
    const video = document.createElement('video');
    video.id = 'video';
    video.autoplay = true;
    video.style.borderRadius = '20px';
    video.style.maxWidth = '90%';
    video.style.maxHeight = '70%';
    modal.appendChild(video);

    const captureBtn = document.createElement('button');
    captureBtn.className = 'btn';
    captureBtn.innerText = 'Take photo';
    modal.appendChild(captureBtn);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-secondary';
    closeBtn.innerText = 'Cancel';
    closeBtn.style.marginTop = '10px';
    modal.appendChild(closeBtn);

    document.body.appendChild(modal);

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;

            captureBtn.onclick = () => {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const dataURL = canvas.toDataURL('image/png');

                const preview = document.getElementById('photoPreview');
                preview.innerHTML = `<img src="${dataURL}" alt="Preview">`;

                const photoInput = document.getElementById('photoInput');
                const dt = new DataTransfer();
                dt.items.add(new File([dataURLToBlob(dataURL)], 'photo.png', { type: 'image/png' }));
                photoInput.files = dt.files;

                stream.getTracks().forEach(track => track.stop());
                modal.remove();
            };

            closeBtn.onclick = () => {
                stream.getTracks().forEach(track => track.stop());
                modal.remove();
            };
        })
        .catch(err => {
            alert('Could not access camera: ' + err);
            modal.remove();
        });
}

// Converts DataURL to Blob
function dataURLToBlob(dataURL) {
    const [meta, content] = dataURL.split(',');
    const mime = meta.match(/:(.*?);/)[1];
    const binary = atob(content);
    const array = [];
    for (let i = 0; i < binary.length; i++) array.push(binary.charCodeAt(i));
    return new Blob([new Uint8Array(array)], { type: mime });
}

// ==== Translation dictionary for garment names ====
// Maps Spanish internal names to English display names
const garmentTranslations = {
    // tops
    'camiseta': 't-shirt', 'camisa': 'shirt', 'blusa': 'blouse',
    'jersey': 'jumper', 'suéter': 'sweater', 'sudadera': 'sweatshirt',
    'blazer': 'blazer', 'chaqueta': 'jacket', 'abrigo': 'coat',
    'top': 'top', 'chaleco': 'vest',
    // bottoms
    'pantalón': 'trousers', 'pantalon': 'trousers', 'vaqueros': 'jeans',
    'falda': 'skirt', 'shorts': 'shorts', 'mallas': 'leggings',
    'leggings': 'leggings', 'pana': 'corduroy trousers',
    // dresses
    'vestido': 'dress',
    // footwear
    'zapatillas': 'trainers', 'botas': 'boots', 'tacones': 'heels',
    'sandalias': 'sandals', 'mocasines': 'loafers', 'zapatos': 'shoes',
    'botines': 'ankle boots',
    // accessories
    'bolso': 'handbag', 'bolsa': 'bag', 'cinturón': 'belt',
    'bufanda': 'scarf', 'gorro': 'hat', 'gafas': 'sunglasses',
    'collar': 'necklace', 'pendientes': 'earrings',
    // colours
    'blanco': 'white', 'negro': 'black', 'gris': 'grey',
    'azul': 'blue', 'rojo': 'red', 'verde': 'green',
    'marrón': 'brown', 'beige': 'beige', 'rosa': 'pink',
    'coral': 'coral', 'dorado': 'gold', 'plateado': 'silver',
    // fit
    'ajustada': 'fitted', 'normal': 'regular', 'holgada': 'loose',
    // gender
    'hombre': 'male', 'mujer': 'female', 'prefiero no decirlo': 'prefer not to say',
    // occasion
    'formal': 'formal', 'casual': 'casual', 'deportiva': 'sport',
    // climate
    'calor': 'hot', 'templado': 'mild', 'frio': 'cold',
    // seasons
    'primavera': 'Spring', 'verano': 'Summer', 'otoño': 'Autumn', 'invierno': 'Winter'
};

function translateValue(value) {
    if (!value) return value;
    const lower = value.toLowerCase().trim();
    return garmentTranslations[lower] || value;
}

// ==== Show summary ====
function showSummary() {
    const summaryBox = document.getElementById('summaryBox');
    let summaryHTML = `
        <h3 style="margin-bottom:20px; color:#7B68EE; text-align:center;">Your profile summary</h3>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 16px;">
    `;

    if (formData.nombre) {
        summaryHTML += `<p style="margin: 8px 0;"><strong>Name:</strong> ${formData.nombre}</p>`;
    }
    if (formData.genero) {
        summaryHTML += `<p style="margin: 8px 0;"><strong>Gender:</strong> ${translateValue(formData.genero)}</p>`;
    }
    if (formData.provincia && formData.mes) {
        summaryHTML += `<p style="margin: 8px 0;"><strong>Location:</strong> ${formData.provincia}, ${formData.mes}</p>`;
    }
    if (formData.ocasion) {
        summaryHTML += `<p style="margin: 8px 0;"><strong>Occasion:</strong> ${translateValue(formData.ocasion)}</p>`;
    }
    if (formData.fit) {
        summaryHTML += `<p style="margin: 8px 0;"><strong>Fit preference:</strong> ${translateValue(formData.fit)}</p>`;
    }

    summaryHTML += `</div>`;

    summaryHTML += `
        <div style="background: #e8f4f8; padding: 16px; border-radius: 12px; border-left: 4px solid #7B68EE; margin-top: 16px;">
            <p style="margin: 0; color: #555; font-size: 14px;">
                <strong>We will analyse your photo</strong> to determine your personalised colourimetry and
                <strong>look up the climate data</strong> for ${formData.provincia || 'your location'}
                in ${formData.mes || 'the selected month'} to create your perfect recommendation.
            </p>
        </div>
    `;

    summaryBox.innerHTML = summaryHTML;
}

// ==== Form submission ====
document.getElementById('onboardingForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    document.getElementById('loading').style.display = 'flex';

    const fd = new FormData();
    for (let key in formData) fd.append(key, formData[key]);

    const photoInput = document.getElementById('photoInput');
    if (photoInput.files && photoInput.files[0]) fd.append('photo', photoInput.files[0]);

    try {
        const response = await fetch('/api/onboarding', { method: 'POST', body: fd });
        const data = await response.json();
        if (data.success) window.location.href = '/results';
        else {
            alert('Error: ' + data.message);
            document.getElementById('loading').style.display = 'none';
        }
    } catch (error) {
        alert('Error processing the request');
        console.error(error);
        document.getElementById('loading').style.display = 'none';
    }
});