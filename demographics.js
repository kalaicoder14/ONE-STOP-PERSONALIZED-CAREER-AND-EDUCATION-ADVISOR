function toggleStreamField(isInitial = false) {
    const level = document.getElementById('education_level').value;
    const streamContainer = document.getElementById('stream_container');
    const marksContainer = document.getElementById('marks_container');

    if (level === '12th') {
        streamContainer.style.display = 'block';
        const stream = document.getElementById('stream').value;
        if (stream) {
            marksContainer.style.display = 'block';
            hideAllSubjects(!isInitial); // Clear values only if NOT initial load
            showSubjectsForStream(stream);
        } else {
            marksContainer.style.display = 'none';
        }
    } else if (level === '10th') {
        streamContainer.style.display = 'none';
        if (!isInitial) {
            const streamEl = document.getElementById('stream');
            if (streamEl) streamEl.value = "";
        }
        marksContainer.style.display = 'block';
        hideAllSubjects(!isInitial);
        showSubjectsForStream('10th');
    } else {
        streamContainer.style.display = 'none';
        if (!isInitial) {
            const streamEl = document.getElementById('stream');
            if (streamEl) streamEl.value = "";
        }
        marksContainer.style.display = 'none';
    }
}

function toggleSubjectFields() {
    const stream = document.getElementById('stream').value;
    const marksContainer = document.getElementById('marks_container');

    if (stream) {
        marksContainer.style.display = 'block';
        hideAllSubjects(true); // User changed stream, clear other subject fields
        showSubjectsForStream(stream);
    } else {
        marksContainer.style.display = 'none';
    }
}

function hideAllSubjects(clearValues = false) {
    document.querySelectorAll('.subject-field').forEach(function (el) {
        el.style.display = 'none';
        const input = el.querySelector('input[type="number"]');
        if (input) {
            input.required = false; // Hidden fields are not required
            input.max = 100; // Requirement: marks out of 100
            input.min = 0;
            if (clearValues) {
                input.value = 0;
            }
        }
    });
}

function showSubjectsForStream(stream) {
    const streamMap = {
        '10th': ['field-lang', 'field-maths', 'field-science', 'field-social'],
        'PCMB': ['field-lang', 'field-physics', 'field-chemistry', 'field-maths', 'field-biology'],
        'PCMC': ['field-lang', 'field-physics', 'field-chemistry', 'field-maths', 'field-cs'],
        'PCB': ['field-lang', 'field-physics', 'field-chemistry', 'field-botany', 'field-zoology'],
        'Commerce': ['field-lang', 'field-accountancy', 'field-economics', 'field-commerce', 'field-ca']
    };

    const header = document.getElementById('marks_header');
    if (header) {
        header.textContent = stream === '10th' ? '10th Standard Subjects' : 'Subjects for ' + stream;
    }

    const fields = streamMap[stream] || [];
    fields.forEach(function (cls) {
        document.querySelectorAll('.' + cls).forEach(function (el) {
            el.style.display = 'block';
            const input = el.querySelector('input[type="number"]');
            if (input) {
                input.required = true; // Visible subjects are mandatory
            }
        });
    });

    calculateTotal();
}

function calculateTotal() {
    let total = 0;
    const level = document.getElementById('education_level').value;

    // Calculate total only from VISIBLE subject fields
    document.querySelectorAll('.subject-field').forEach(function (fieldDiv) {
        if (fieldDiv.style.display !== 'none') {
            const input = fieldDiv.querySelector('input[type="number"]');
            if (input) {
                total += parseFloat(input.value || 0);
            }
        }
    });

    const totalField = document.getElementById('total_marks');
    if (totalField) {
        totalField.value = total.toFixed(2);
    }

    // Update Maximum Marks automatically
    const maxMarksField = document.getElementById('max_marks');
    if (maxMarksField) {
        if (level === '12th') {
            maxMarksField.value = 600;
        } else if (level === '10th') {
            maxMarksField.value = 500;
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const levelEl = document.getElementById('education_level');
    const marksContainer = document.getElementById('marks_container');

    if (!levelEl) return;

    // Set initial state based on existing data
    toggleStreamField(true);

    // Listen for any input changes to update total
    if (marksContainer) {
        marksContainer.addEventListener('input', function (e) {
            if (e.target.type === 'number') {
                calculateTotal();
            }
        });
    }
});