/* ===== MIDI Cleaner — Frontend Application ===== */

// ─────────────────────────────────────────────
//  Internationalization
// ─────────────────────────────────────────────
const I18N = {
    en: {
        title: 'Cleaner', subtitle: 'Clean multi-track MIDI files from AI transcription artifacts',
        drop_zone: 'Drop MIDI file here or click to browse', drop_replace: 'Click or drop to replace',
        processing_settings: 'Processing Settings',
        merge_voices: 'Merge Voices', merge_voices_desc: 'Consolidate all voices to voice 1 per track',
        remove_overlaps: 'Remove Overlaps', remove_overlaps_desc: 'Merge overlapping same-pitch notes',
        remove_triplets: 'Remove Triplets', remove_triplets_desc: 'Convert triplet notes to straight eighths',
        triplet_tolerance: 'Triplet Tolerance', triplet_tolerance_desc: 'Detection sensitivity (0.05=strict, 0.25=loose)',
        quantize: 'Quantize', quantize_desc: 'Snap note timing to rhythmic grid',
        grid_resolution: 'Grid Resolution', grid_resolution_desc: 'Quantization grid size',
        quarter: 'Quarter note', eighth: 'Eighth note', sixteenth: 'Sixteenth note',
        remove_cc: 'Remove CC Messages', remove_cc_desc: 'Strip control change messages',
        cc_to_remove: 'CC Numbers to Remove', cc_to_remove_desc: 'Select which CC to strip',
        pitch_cluster: 'Pitch Cluster', pitch_cluster_desc: 'Merge near-pitch simultaneous notes (AI transcription noise)',
        pitch_cluster_window: 'Time Window (ticks)', pitch_cluster_window_desc: 'Max onset spread for notes to be considered simultaneous',
        pitch_cluster_threshold: 'Pitch Threshold (semitones)', pitch_cluster_threshold_desc: 'Max semitone distance within a cluster',
        noise_filter: 'Noise Filter', noise_filter_desc: 'Remove short and quiet parasitic notes',
        min_duration: 'Min Note Duration (ticks)', min_duration_desc: 'Notes shorter than this are removed',
        min_velocity: 'Min Velocity', min_velocity_desc: 'Notes quieter than this are removed',
        same_pitch_overlap: 'Same-Pitch Overlap Resolver', same_pitch_overlap_desc: 'Remove duplicate overlapping notes of the same pitch per channel',
        tempo_dedup: 'Deduplicate Tempo', tempo_dedup_desc: 'Remove redundant tempo markings (fixes ♩=91 spam)',
        start_bar: 'Start Processing from Bar', start_bar_desc: 'Skip already-cleaned bars (1 = all)',
        merge_tracks: 'Merge All Tracks', merge_tracks_desc: 'Flatten into a single track (Type 0) for manual editing',
        merge_tracks_cc: 'Include CC in Merge', merge_tracks_cc_desc: 'Keep CC events in the merged output',
        merge_cc_whitelist: 'Merge CC Whitelist', merge_cc_whitelist_desc: 'Which CC numbers to keep (uncheck all = keep all)',
        player_title: 'Player', original: 'Original', processed: 'Processed',
        tracks: 'Tracks', notes: 'notes', show_notation: 'Show Notation',
        play: 'Play', stop: 'Stop', play_processed: 'Play Processed',
        process_btn: 'Process & Clean', download_btn: 'Download',
        shorter_removed: 'Shorter notes removed', quieter_removed: 'Quieter notes removed',
        min_dur_ticks: 'Min Duration (ticks)', min_vel: 'Min Velocity',
        auto_optimize: 'Auto Optimize',
        opt_max_trials: 'Max Trials', opt_max_trials_desc: 'Maximum optimization iterations (1–100)',
        opt_start: 'Start Optimization', opt_trial: 'Trial', opt_best_score: 'Best Score',
        opt_track_type: 'Track Type', opt_status_label: 'Status', opt_running: 'Running...',
        opt_current_params: 'Current Best Parameters', opt_apply: 'Apply Best Parameters',
        opt_done: 'Done', opt_stopped: 'Stopped', opt_error: 'Error',
        opt_applied: 'Optimized parameters applied! Click Download.',
        preset_label: 'Preset', preset_auto: 'Auto (Recommended)',
        lock_advanced: 'Show Advanced',
        processing_log: 'Processing Log', log_total_time: 'Total Time:',
        log_notes_in: 'Notes In:', log_notes_out: 'Notes Out:', log_preset: 'Preset:',
        log_step: 'Step', log_enabled: 'On', log_duration: 'Time (ms)',
        log_in: 'In', log_out: 'Out', log_removed: 'Removed', log_detail: 'Detail',
        download_report: 'Download report.json',
        llm_guidance: 'LLM Guidance', llm_guidance_desc: 'Use GPT-4o-mini as strategy advisor when optimizer stalls',
        llm_suggestions: 'LLM Suggestions',
        loaded_msg: 'Loaded', processing_msg: 'Processing...', process_done: 'Processing complete! Click Download.',
        no_notes: 'No notes to play', upload_fail: 'Upload failed', process_fail: 'Processing failed',
        loading_notation: 'Loading notation...', no_notes_track: 'No notes in this track',
    },
    ru: {
        title: 'Очистка', subtitle: 'Очистка многодорожечных MIDI файлов от артефактов AI транскрипции',
        drop_zone: 'Перетащите MIDI файл сюда или нажмите для выбора', drop_replace: 'Нажмите или перетащите для замены',
        processing_settings: 'Настройки обработки',
        merge_voices: 'Объединить голоса', merge_voices_desc: 'Свести все голоса в голос 1 для каждой дорожки',
        remove_overlaps: 'Убрать наложения', remove_overlaps_desc: 'Объединить наложенные ноты одного тона',
        remove_triplets: 'Убрать триоли', remove_triplets_desc: 'Конвертировать триоли в прямые восьмые',
        triplet_tolerance: 'Точность триолей', triplet_tolerance_desc: 'Чувствительность (0.05=строго, 0.25=свободно)',
        quantize: 'Квантизация', quantize_desc: 'Выровнять ноты по ритмической сетке',
        grid_resolution: 'Разрешение сетки', grid_resolution_desc: 'Размер ячейки квантизации',
        quarter: 'Четвертная', eighth: 'Восьмая', sixteenth: 'Шестнадцатая',
        remove_cc: 'Удалить CC сообщения', remove_cc_desc: 'Удалить Control Change сообщения',
        cc_to_remove: 'Номера CC для удаления', cc_to_remove_desc: 'Выберите какие CC удалить',
        pitch_cluster: 'Кластер высот', pitch_cluster_desc: 'Объединить близкие по высоте одновременные ноты (шум AI транскрипции)',
        pitch_cluster_window: 'Временное окно (тики)', pitch_cluster_window_desc: 'Макс. разброс начала нот для группировки',
        pitch_cluster_threshold: 'Порог высоты (полутоны)', pitch_cluster_threshold_desc: 'Макс. расстояние в полутонах внутри кластера',
        noise_filter: 'Фильтр шума', noise_filter_desc: 'Удалить короткие и тихие паразитные ноты',
        min_duration: 'Мин. длительность (тики)', min_duration_desc: 'Ноты короче этого удаляются',
        min_velocity: 'Мин. громкость', min_velocity_desc: 'Ноты тише этого удаляются',
        same_pitch_overlap: 'Разрешение наложений одной высоты', same_pitch_overlap_desc: 'Удалить дублирующиеся наложенные ноты одной высоты',
        tempo_dedup: 'Дедупликация темпа', tempo_dedup_desc: 'Удалить повторяющиеся темповые метки (убирает ♩=91 спам)',
        start_bar: 'Начать с такта', start_bar_desc: 'Пропустить очищенные такты (1 = всё)',
        merge_tracks: 'Объединить дорожки', merge_tracks_desc: 'Слить все дорожки в одну (Type 0) для ручной правки',
        merge_tracks_cc: 'CC в объединении', merge_tracks_cc_desc: 'Сохранить CC события в объединённом выводе',
        merge_cc_whitelist: 'CC белый список', merge_cc_whitelist_desc: 'Какие CC номера сохранить (без выбора = все)',
        player_title: 'Плеер', original: 'Оригинал', processed: 'Обработанный',
        tracks: 'Дорожки', notes: 'нот', show_notation: 'Ноты',
        play: 'Воспр.', stop: 'Стоп', play_processed: 'Воспр. обработанный',
        process_btn: 'Обработать', download_btn: 'Скачать',
        shorter_removed: 'Короткие ноты удаляются', quieter_removed: 'Тихие ноты удаляются',
        min_dur_ticks: 'Мин. длительность (тики)', min_vel: 'Мин. громкость',
        auto_optimize: 'Авто-оптимизация',
        opt_max_trials: 'Макс. итераций', opt_max_trials_desc: 'Максимальное число итераций оптимизации (1–100)',
        opt_start: 'Запустить оптимизацию', opt_trial: 'Итерация', opt_best_score: 'Лучший балл',
        opt_track_type: 'Тип дорожки', opt_status_label: 'Статус', opt_running: 'Выполняется...',
        opt_current_params: 'Лучшие параметры', opt_apply: 'Применить лучшие параметры',
        opt_done: 'Готово', opt_stopped: 'Остановлено', opt_error: 'Ошибка',
        opt_applied: 'Оптимизированные параметры применены! Нажмите Скачать.',
        preset_label: 'Пресет', preset_auto: 'Авто (рекомендуемый)',
        lock_advanced: 'Показать расширенные',
        processing_log: 'Лог обработки', log_total_time: 'Общее время:',
        log_notes_in: 'Нот на входе:', log_notes_out: 'Нот на выходе:', log_preset: 'Пресет:',
        log_step: 'Шаг', log_enabled: 'Вкл.', log_duration: 'Время (мс)',
        log_in: 'Вход', log_out: 'Выход', log_removed: 'Удалено', log_detail: 'Детали',
        download_report: 'Скачать report.json',
        llm_guidance: 'LLM подсказки', llm_guidance_desc: 'Использовать GPT-4o-mini как советника при застое оптимизатора',
        llm_suggestions: 'LLM подсказки',
        loaded_msg: 'Загружен', processing_msg: 'Обработка...', process_done: 'Готово! Нажмите Скачать.',
        no_notes: 'Нет нот для воспроизведения', upload_fail: 'Ошибка загрузки', process_fail: 'Ошибка обработки',
        loading_notation: 'Загрузка нотации...', no_notes_track: 'Нет нот в дорожке',
    },
};

let currentLang = 'en';
function t(key) { return I18N[currentLang][key] || key; }

function applyLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const k = el.dataset.i18n;
        if (I18N[currentLang][k]) el.textContent = I18N[currentLang][k];
    });
    document.querySelectorAll('[data-i18n-opt]').forEach(el => {
        const k = el.dataset.i18nOpt;
        if (I18N[currentLang][k]) el.textContent = I18N[currentLang][k];
    });
    if (state.fileUploaded && state.fileInfo) showTracks(state.fileInfo.tracks);
}

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'ru' : 'en';
    document.getElementById('lang-toggle').textContent = currentLang === 'en' ? 'RU' : 'EN';
    applyLanguage();
}

// ─────────────────────────────────────────────
//  State
// ─────────────────────────────────────────────
const state = {
    fileUploaded: false,
    fileInfo: null,
    processing: false,
    processed: false,
    notationCache: {},
    playbackCache: {},
    activePlayers: {},
    fullPlayerSource: 'original',
    fullPlayerData: null,
    // Full player runtime
    fullPlayerSynths: null,
    fullPlayerDuration: 0,
    fullPlayerAnimFrame: null,
    fullPlayerPlaying: false,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function toast(msg, type = 'info') {
    const c = $('.toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

// ─────────────────────────────────────────────
//  Upload
// ─────────────────────────────────────────────
function initUpload() {
    const zone = $('#drop-zone');
    const input = zone.querySelector('input[type="file"]');
    if (!input) return;
    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault(); zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', () => { if (input.files.length > 0) uploadFile(input.files[0]); });
}

async function uploadFile(file) {
    if (!file.name.toLowerCase().match(/\.midi?$/)) { toast(t('upload_fail'), 'error'); return; }
    const zone = $('#drop-zone');
    zone.innerHTML = `<div class="spinner"></div><p>${file.name}...</p>`;

    const form = new FormData();
    form.append('file', file);
    try {
        const resp = await fetch('/api/upload', { method: 'POST', body: form });
        const data = await resp.json();
        if (!resp.ok) { toast(data.error || t('upload_fail'), 'error'); resetDropZone(); return; }

        cleanupAllAudio();
        state.fileUploaded = true;
        state.fileInfo = data;
        state.processed = false;
        state.notationCache = {};
        state.playbackCache = {};
        state.fullPlayerData = null;

        zone.innerHTML = `<div class="icon">&#9835;</div><p>${t('loaded_msg')}: <strong>${data.filename}</strong></p><p class="filename">${t('drop_replace')}</p><input type="file" accept=".mid,.midi">`;
        initUpload();

        showFileInfo(data);
        showConfig();
        showOptimizePanel();
        showTracks(data.tracks);
        showActionBar();
        showPlayerSection();
        suggestPreset();
        toast(`${t('loaded_msg')} ${data.filename}: ${data.num_tracks} ${t('tracks').toLowerCase()}`, 'success');
    } catch (err) {
        toast(t('upload_fail') + ': ' + err.message, 'error'); resetDropZone();
    }
}

function resetDropZone() {
    const zone = $('#drop-zone');
    zone.innerHTML = `<div class="icon">&#128196;</div><p data-i18n="drop_zone">${t('drop_zone')}</p><input type="file" accept=".mid,.midi">`;
    initUpload();
}

// ─────────────────────────────────────────────
//  File Info
// ─────────────────────────────────────────────
function showFileInfo(data) {
    const bar = $('.file-info');
    bar.innerHTML = `<span class="tag">Format: <strong>Type ${data.type}</strong></span><span class="tag">PPQ: <strong>${data.ticks_per_beat}</strong></span><span class="tag">${t('tracks')}: <strong>${data.num_tracks}</strong></span>`;
    bar.classList.add('visible');
}

// ─────────────────────────────────────────────
//  Configuration
// ─────────────────────────────────────────────
function showConfig() { $('.config-panel').classList.add('visible'); }

function readGlobalConfig() {
    const presetEl = $('#cfg-preset');
    return {
        _preset: presetEl ? presetEl.value : '',
        tempo_deduplicator: { enabled: $('#cfg-tempo-dedup').checked },
        merge_voices: $('#cfg-merge-voices').checked,
        remove_overlaps: $('#cfg-remove-overlaps').checked,
        remove_triplets: $('#cfg-remove-triplets').checked,
        triplet_tolerance: parseFloat($('#cfg-triplet-tolerance').value),
        quantize: $('#cfg-quantize').checked,
        quantize_grid: $('#cfg-quantize-grid').value,
        remove_cc: $('#cfg-remove-cc').checked,
        cc_numbers: [$('#cfg-cc-64').checked && 64, $('#cfg-cc-68').checked && 68].filter(Boolean),
        pitch_cluster: {
            enabled: $('#cfg-pitch-cluster').checked,
            time_window_ticks: parseInt($('#cfg-pitch-cluster-window').value),
            pitch_threshold: parseInt($('#cfg-pitch-cluster-threshold').value),
        },
        filter_noise: $('#cfg-filter-noise').checked,
        min_duration_ticks: parseInt($('#cfg-min-duration').value),
        min_velocity: parseInt($('#cfg-min-velocity').value),
        same_pitch_overlap_resolver: { enabled: $('#cfg-same-pitch-overlap').checked },
        start_bar: parseInt($('#cfg-start-bar').value),
        merge_tracks: {
            enabled: $('#cfg-merge-tracks').checked,
            include_cc: $('#cfg-merge-cc').checked,
            cc_whitelist: [$('#cfg-merge-cc-64').checked && 64, $('#cfg-merge-cc-68').checked && 68].filter(Boolean),
        },
        track_overrides: readTrackOverrides(),
    };
}

function readTrackOverrides() {
    const ov = {};
    $$('.track-card').forEach(card => {
        const idx = card.dataset.trackIdx;
        if (!card.querySelector('.track-toggle')?.checked) {
            ov[idx] = { merge_voices:false, remove_triplets:false, quantize:false, remove_cc:false, filter_noise:false };
            return;
        }
        const d = card.querySelector('.track-min-duration');
        const v = card.querySelector('.track-min-velocity');
        if (d || v) { ov[idx] = {}; if (d) ov[idx].min_duration_ticks = +d.value; if (v) ov[idx].min_velocity = +v.value; }
    });
    return ov;
}

function initSliders() {
    $$('input[type="range"]').forEach(sl => {
        const disp = sl.parentElement.querySelector('.value');
        if (disp) { disp.textContent = sl.value; sl.addEventListener('input', () => disp.textContent = sl.value); }
    });
}

// ─────────────────────────────────────────────
//  Tracks List
// ─────────────────────────────────────────────
function showTracks(tracks) {
    const list = $('.tracks-list');
    list.innerHTML = `<h2>${t('tracks')}</h2>`;
    tracks.forEach(tr => {
        // Skip tempo/meta tracks with no notes
        if (!tr.has_notes) return;
        list.appendChild(createTrackCard(tr));
    });
    list.classList.add('visible');
    initSliders();
}

function getPlaySource() {
    // Always compute the current source dynamically
    return state.processed ? 'processed' : 'original';
}

function createTrackCard(track) {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.dataset.trackIdx = track.index;
    const sug = track.suggested_thresholds || {};
    const noteRange = track.note_range || [0, 0];
    const channels = (track.channels_used || []).join(', ');

    card.innerHTML = `
        <div class="track-header">
            <input type="checkbox" class="track-toggle" checked>
            <span class="track-name">${escHtml(track.name)}</span>
            <span class="track-type ${track.track_type}">${track.track_type.toUpperCase()}</span>
            <span class="track-meta"><span>${track.note_count} ${t('notes')}</span><span>ch: ${channels || track.channel}</span><span>${noteRange[0]}-${noteRange[1]}</span></span>
            <button class="expand-btn">&#9660;</button>
        </div>
        <div class="track-details">
            <div class="track-config">
                <div class="config-item"><label>${t('min_dur_ticks')}<span class="desc">${t('shorter_removed')}</span></label><div class="range-group"><input type="range" class="track-min-duration" min="0" max="480" step="10" value="${sug.min_duration_ticks||120}"><span class="value">${sug.min_duration_ticks||120}</span></div></div>
                <div class="config-item"><label>${t('min_vel')}<span class="desc">${t('quieter_removed')}</span></label><div class="range-group"><input type="range" class="track-min-velocity" min="0" max="127" step="1" value="${sug.min_velocity||20}"><span class="value">${sug.min_velocity||20}</span></div></div>
            </div>
            <div class="track-controls">
                <button class="btn-notation">${t('show_notation')}</button>
                <button class="btn-play">${t('play')}</button>
                <button class="btn-stop" style="display:none">${t('stop')}</button>
            </div>
            <div class="comparison-tabs" ${state.processed ? '' : 'style="display:none"'}>
                <button class="tab-original active">${t('original')}</button>
                <button class="tab-processed">${t('processed')}</button>
            </div>
            <div class="notation-container" id="notation-${track.index}"></div>
        </div>`;

    const header = card.querySelector('.track-header');
    header.addEventListener('click', e => { if (!e.target.classList.contains('track-toggle')) card.classList.toggle('expanded'); });
    // Use getPlaySource() dynamically so it always uses the correct source
    card.querySelector('.btn-notation').addEventListener('click', e => { e.stopPropagation(); loadNotation(track.index, getPlaySource()); });
    card.querySelector('.btn-play').addEventListener('click', e => { e.stopPropagation(); playTrack(track.index, getPlaySource()); });
    card.querySelector('.btn-stop').addEventListener('click', e => { e.stopPropagation(); stopTrack(track.index); });
    card.querySelector('.tab-original').addEventListener('click', () => { loadNotation(track.index, 'original'); card.querySelector('.tab-original').classList.add('active'); card.querySelector('.tab-processed').classList.remove('active'); });
    card.querySelector('.tab-processed').addEventListener('click', () => { loadNotation(track.index, 'processed'); card.querySelector('.tab-processed').classList.add('active'); card.querySelector('.tab-original').classList.remove('active'); });

    setTimeout(() => {
        card.querySelectorAll('input[type="range"]').forEach(sl => {
            const d = sl.parentElement.querySelector('.value');
            if (d) sl.addEventListener('input', () => d.textContent = sl.value);
        });
    }, 0);
    return card;
}

// ─────────────────────────────────────────────
//  Action Bar & Processing
// ─────────────────────────────────────────────
function showActionBar() { $('.action-bar').classList.add('visible'); }

async function processFile() {
    if (state.processing) return;
    state.processing = true;
    const btn = $('#btn-process');
    const statusEl = $('.action-bar .status');
    btn.disabled = true;
    statusEl.innerHTML = `<div class="spinner"></div> ${t('processing_msg')}`;
    cleanupAllAudio();

    try {
        const resp = await fetch('/api/process', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(readGlobalConfig()) });
        const data = await resp.json();
        if (!resp.ok) { toast(data.error || t('process_fail'), 'error'); return; }

        state.processed = true;
        state.notationCache = {};
        state.playbackCache = {};
        state.fullPlayerData = null;
        statusEl.innerHTML = '';
        $('#btn-download').style.display = 'inline-flex';
        $('#player-src-processed').disabled = false;

        // Update track data for display
        if (state.fileInfo) {
            state.fileInfo.tracks.forEach((orig, i) => {
                const pt = data.tracks[i];
                if (pt) {
                    orig.note_count = pt.note_count;
                    orig.channels_used = pt.channels_used;
                    orig.note_range = pt.note_range;
                }
            });
        }
        showTracks(state.fileInfo.tracks);
        $$('.comparison-tabs').forEach(el => el.style.display = 'flex');

        if (data.report) showProcessingLog(data.report);
        toast(t('process_done'), 'success');
    } catch (err) {
        toast(t('process_fail') + ': ' + err.message, 'error');
    } finally {
        state.processing = false;
        btn.disabled = false;
    }
}

function downloadFile() { window.location.href = '/api/download'; }

// ─────────────────────────────────────────────
//  Auto Optimize
// ─────────────────────────────────────────────
let optimizePollTimer = null;

function showOptimizePanel() {
    const panel = $('#optimize-panel');
    if (panel) panel.classList.add('visible');
}

async function startOptimization() {
    const btn = $('#btn-optimize');
    const statusEl = $('#optimize-status');
    const doneActions = $('#optimize-done-actions');
    btn.disabled = true;
    doneActions.style.display = 'none';
    statusEl.style.display = 'block';
    $('#opt-trial').textContent = '0 / ?';
    $('#opt-best-score').innerHTML = '&mdash;';
    $('#opt-track-type').innerHTML = '&mdash;';
    $('#opt-status-text').innerHTML = `<div class="spinner" style="display:inline-block;vertical-align:middle"></div> ${t('opt_running')}`;
    $('#opt-params-json').textContent = '{}';

    const maxTrials = parseInt($('#opt-max-trials').value) || 40;

    try {
        const resp = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                max_trials: maxTrials,
                llm: { enabled: $('#cfg-llm-enabled') ? $('#cfg-llm-enabled').checked : false },
            }),
        });
        const data = await resp.json();
        if (!resp.ok) {
            toast(data.error || t('process_fail'), 'error');
            btn.disabled = false;
            return;
        }
        pollOptimizationStatus();
    } catch (err) {
        toast(t('process_fail') + ': ' + err.message, 'error');
        btn.disabled = false;
    }
}

function pollOptimizationStatus() {
    if (optimizePollTimer) clearInterval(optimizePollTimer);
    optimizePollTimer = setInterval(async () => {
        try {
            const resp = await fetch('/api/optimize/status');
            const data = await resp.json();
            updateOptimizeUI(data);
            if (data.status === 'done' || data.status === 'error' || data.status === 'idle') {
                clearInterval(optimizePollTimer);
                optimizePollTimer = null;
                $('#btn-optimize').disabled = false;
            }
        } catch (err) {
            clearInterval(optimizePollTimer);
            optimizePollTimer = null;
            $('#btn-optimize').disabled = false;
        }
    }, 800);
}

function updateOptimizeUI(data) {
    $('#opt-trial').textContent = `${data.current_trial || 0} / ${data.total_trials || '?'}`;
    if (data.best_score != null) {
        $('#opt-best-score').textContent = data.best_score.toFixed(4);
    }
    if (data.track_type) {
        $('#opt-track-type').textContent = data.track_type.toUpperCase();
    }
    if (data.current_params && Object.keys(data.current_params).length > 0) {
        $('#opt-params-json').textContent = JSON.stringify(data.current_params, null, 2);
    }

    if (data.status === 'done') {
        const reason = data.stop_reason ? ` (${data.stop_reason})` : '';
        $('#opt-status-text').innerHTML = `<span style="color:var(--success)">${t('opt_done')}${reason}</span>`;
        $('#optimize-done-actions').style.display = 'flex';
        if (data.best_params && Object.keys(data.best_params).length > 0) {
            $('#opt-params-json').textContent = JSON.stringify(data.best_params, null, 2);
        }
    } else if (data.status === 'error') {
        $('#opt-status-text').innerHTML = `<span style="color:var(--danger)">${t('opt_error')}: ${data.error || 'unknown'}</span>`;
    } else {
        $('#opt-status-text').innerHTML = `<div class="spinner" style="display:inline-block;vertical-align:middle"></div> ${t('opt_running')}`;
    }

    if (data.llm_decisions) updateLLMSuggestionsUI(data.llm_decisions);
}

async function applyOptimized() {
    try {
        const resp = await fetch('/api/optimize/apply', { method: 'POST' });
        const data = await resp.json();
        if (!resp.ok) { toast(data.error || t('process_fail'), 'error'); return; }

        state.processed = true;
        state.notationCache = {};
        state.playbackCache = {};
        state.fullPlayerData = null;
        $('#btn-download').style.display = 'inline-flex';
        $('#player-src-processed').disabled = false;

        if (state.fileInfo && data.tracks) {
            state.fileInfo.tracks.forEach((orig, i) => {
                const pt = data.tracks[i];
                if (pt) {
                    orig.note_count = pt.note_count;
                    orig.channels_used = pt.channels_used;
                    orig.note_range = pt.note_range;
                }
            });
        }
        showTracks(state.fileInfo.tracks);
        $$('.comparison-tabs').forEach(el => el.style.display = 'flex');
        toast(t('opt_applied'), 'success');
    } catch (err) {
        toast(t('process_fail') + ': ' + err.message, 'error');
    }
}

// ─────────────────────────────────────────────
//  Audio Cleanup Helper
// ─────────────────────────────────────────────
function cleanupAllAudio() {
    // Stop full player
    stopFullPlayerClean();
    // Stop all per-track players
    Object.keys(state.activePlayers).forEach(idx => stopTrack(idx));
}

// ─────────────────────────────────────────────
//  Per-Track Playback (Tone.js — direct scheduling, no Transport)
// ─────────────────────────────────────────────
async function playTrack(trackIdx, source) {
    stopTrack(trackIdx);

    const cacheKey = `${trackIdx}-${source}`;
    let data = state.playbackCache[cacheKey];
    if (!data) {
        try {
            const resp = await fetch(`/api/track/${trackIdx}/playback?source=${source}`);
            if (!resp.ok) { toast(t('no_notes'), 'error'); return; }
            data = await resp.json();
            state.playbackCache[cacheKey] = data;
        } catch (err) { toast(t('no_notes'), 'error'); return; }
    }
    if (!data.notes || data.notes.length === 0) { toast(t('no_notes'), 'info'); return; }

    await Tone.start();
    // Ensure context is running
    if (Tone.context.state !== 'running') {
        await Tone.context.resume();
    }

    const synth = new Tone.PolySynth(Tone.Synth, { maxPolyphony: 64 }).toDestination();
    synth.set({ envelope: { attack: 0.02, decay: 0.3, sustain: 0.4, release: 0.8 } });
    synth.volume.value = -6;

    const now = Tone.now() + 0.15;
    let maxEnd = now;
    const releaseTimeouts = [];
    data.notes.forEach(n => {
        const noteTime = now + n.time;
        const dur = Math.max(n.duration, 0.05);
        try {
            synth.triggerAttack(n.note, noteTime, n.velocity);
            const releaseDelay = (noteTime - Tone.now() + dur) * 1000;
            releaseTimeouts.push(setTimeout(() => {
                try { if (!synth.disposed) synth.triggerRelease(n.note); } catch (e) { /* */ }
            }, Math.max(0, releaseDelay)));
        } catch (e) { /* skip bad note */ }
        maxEnd = Math.max(maxEnd, noteTime + dur);
    });

    const totalMs = (maxEnd - now + 1) * 1000;
    state.activePlayers[trackIdx] = {
        synth,
        releaseTimeouts,
        timeout: setTimeout(() => stopTrack(trackIdx), totalMs),
    };

    const card = $(`.track-card[data-track-idx="${trackIdx}"]`);
    if (card) { card.querySelector('.btn-play').style.display = 'none'; card.querySelector('.btn-stop').style.display = 'inline-flex'; }
}

function stopTrack(trackIdx) {
    const p = state.activePlayers[trackIdx];
    if (p) {
        clearTimeout(p.timeout);
        if (p.releaseTimeouts) p.releaseTimeouts.forEach(t => clearTimeout(t));
        try { if (p.synth && !p.synth.disposed) { p.synth.disconnect(); p.synth.dispose(); } } catch (e) { /* */ }
        delete state.activePlayers[trackIdx];
    }
    const card = $(`.track-card[data-track-idx="${trackIdx}"]`);
    if (card) { card.querySelector('.btn-play').style.display = 'inline-flex'; card.querySelector('.btn-stop').style.display = 'none'; }
}

// ─────────────────────────────────────────────
//  Full MIDI Player (all tracks — uses Tone.Transport)
// ─────────────────────────────────────────────
function showPlayerSection() { $('#player-section').classList.add('visible'); }

async function loadFullPlayback(source) {
    const resp = await fetch(`/api/playback/all?source=${source}`);
    if (!resp.ok) { const d = await resp.json(); throw new Error(d.error || 'Failed'); }
    return await resp.json();
}

async function startFullPlayer() {
    // Full cleanup first
    stopFullPlayerClean();
    await Tone.start();
    if (Tone.context.state !== 'running') await Tone.context.resume();

    const source = state.fullPlayerSource;

    try {
        // Fetch data if needed
        if (!state.fullPlayerData || state.fullPlayerData._source !== source) {
            const data = await loadFullPlayback(source);
            data._source = source;
            state.fullPlayerData = data;
        }
        const data = state.fullPlayerData;
        if (!data.tracks || data.tracks.length === 0) { toast(t('no_notes'), 'info'); return; }

        state.fullPlayerDuration = data.duration || 1;
        $('#player-total').textContent = formatTime(state.fullPlayerDuration);

        // Reset Transport completely
        Tone.Transport.stop();
        Tone.Transport.cancel();
        Tone.Transport.seconds = 0;
        Tone.Transport.bpm.value = data.bpm || 120;

        // Create synths and schedule notes
        const synths = [];
        data.tracks.forEach(tr => {
            const synth = new Tone.PolySynth(Tone.Synth, { maxPolyphony: 48 }).toDestination();
            synth.set({ envelope: { attack: 0.02, decay: 0.25, sustain: 0.3, release: 0.6 } });
            synth.volume.value = -8;
            synths.push(synth);

            tr.notes.forEach(n => {
                const dur = Math.max(n.duration, 0.03);
                Tone.Transport.schedule(time => {
                    try { if (!synth.disposed) synth.triggerAttack(n.note, time, n.velocity); } catch (e) { /* */ }
                }, n.time);
                Tone.Transport.schedule(time => {
                    try { if (!synth.disposed) synth.triggerRelease(n.note, time); } catch (e) { /* */ }
                }, n.time + dur);
            });
        });

        // Schedule auto-stop at end
        Tone.Transport.schedule(() => {
            stopFullPlayerClean();
        }, state.fullPlayerDuration + 0.5);

        state.fullPlayerSynths = synths;
        state.fullPlayerPlaying = true;

        // Start!
        Tone.Transport.start();

        $('#player-play').style.display = 'none';
        $('#player-pause').style.display = 'flex';

        // Start position updater
        updatePlayerPosition();
    } catch (err) {
        console.error('Full player error:', err);
        toast(err.message, 'error');
    }
}

function pauseFullPlayer() {
    if (Tone.Transport.state === 'started') {
        Tone.Transport.pause();
        state.fullPlayerPlaying = false;
        $('#player-play').style.display = 'flex';
        $('#player-pause').style.display = 'none';
    }
}

function resumeOrStartFullPlayer() {
    if (Tone.Transport.state === 'paused' && state.fullPlayerSynths) {
        // Resume from paused position
        Tone.Transport.start();
        state.fullPlayerPlaying = true;
        $('#player-play').style.display = 'none';
        $('#player-pause').style.display = 'flex';
        updatePlayerPosition();
    } else {
        // Fresh start
        startFullPlayer();
    }
}

function stopFullPlayerClean() {
    // Cancel animation frame first
    if (state.fullPlayerAnimFrame) {
        cancelAnimationFrame(state.fullPlayerAnimFrame);
        state.fullPlayerAnimFrame = null;
    }
    state.fullPlayerPlaying = false;

    // Stop transport
    try { Tone.Transport.stop(); } catch (e) { /* */ }
    try { Tone.Transport.cancel(); } catch (e) { /* */ }

    // Dispose synths
    if (state.fullPlayerSynths) {
        state.fullPlayerSynths.forEach(s => {
            try { if (s && !s.disposed) { s.disconnect(); s.dispose(); } } catch (e) { /* */ }
        });
        state.fullPlayerSynths = null;
    }

    // Reset UI
    const playBtn = $('#player-play');
    const pauseBtn = $('#player-pause');
    if (playBtn) playBtn.style.display = 'flex';
    if (pauseBtn) pauseBtn.style.display = 'none';
    const seekBar = $('#player-seek');
    if (seekBar) seekBar.value = 0;
    const curTime = $('#player-current');
    if (curTime) curTime.textContent = '0:00';
}

function rewindFullPlayer() {
    if (state.fullPlayerSynths) {
        // Full restart from beginning
        startFullPlayer();
    }
}

function seekFullPlayer(value) {
    if (state.fullPlayerSynths && state.fullPlayerDuration > 0) {
        // Seeking requires restart because Tone.Transport.schedule is absolute
        // Just update the position indicator for now
        const sec = (value / 1000) * state.fullPlayerDuration;
        try { Tone.Transport.seconds = sec; } catch (e) { /* */ }
    }
}

function updatePlayerPosition() {
    if (!state.fullPlayerPlaying) return;
    const dur = state.fullPlayerDuration || 1;
    const pos = Tone.Transport.seconds;
    const curTime = $('#player-current');
    const seekBar = $('#player-seek');
    if (curTime) curTime.textContent = formatTime(Math.min(pos, dur));
    if (seekBar) seekBar.value = Math.round((Math.min(pos, dur) / dur) * 1000);

    if (Tone.Transport.state === 'started') {
        state.fullPlayerAnimFrame = requestAnimationFrame(updatePlayerPosition);
    }
}

function formatTime(seconds) {
    const m = Math.floor(Math.max(0, seconds) / 60);
    const s = Math.floor(Math.max(0, seconds) % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

// ─────────────────────────────────────────────
//  Notation Rendering (VexFlow + TAB)
// ─────────────────────────────────────────────
async function loadNotation(trackIdx, source) {
    const cacheKey = `${trackIdx}-${source}`;
    const container = $(`#notation-${trackIdx}`);
    container.classList.add('visible');
    container.innerHTML = `<div style="text-align:center;padding:20px;color:#666"><div class="spinner" style="margin:0 auto 8px"></div>${t('loading_notation')}</div>`;

    let data = state.notationCache[cacheKey];
    if (!data) {
        try {
            const resp = await fetch(`/api/track/${trackIdx}/notation?source=${source}&measures=64`);
            data = await resp.json();
            if (resp.ok) state.notationCache[cacheKey] = data;
        } catch (err) { container.innerHTML = `<p style="color:red;padding:12px">${err.message}</p>`; return; }
    }
    if (data.error) { container.innerHTML = `<p style="color:red;padding:12px">${data.error}</p>`; return; }
    renderNotation(container, data);
}

function renderNotation(container, data) {
    container.innerHTML = '';
    if (!data.measures || data.measures.length === 0) {
        container.innerHTML = `<p style="color:#666;padding:12px">${t('no_notes_track')}</p>`; return;
    }

    const VF = Vex.Flow;
    const showTab = !!data.show_tab;
    const measuresPerLine = 4;
    const staveWidth = 250;
    const staveHeight = showTab ? 230 : 140;
    const tabOffset = 110;
    const leftMargin = 10;
    const topMargin = 20;
    const numLines = Math.ceil(data.measures.length / measuresPerLine);
    const totalWidth = leftMargin + measuresPerLine * staveWidth + 20;
    const totalHeight = topMargin + numLines * staveHeight + 20;

    const div = document.createElement('div');
    div.style.minWidth = totalWidth + 'px';
    container.appendChild(div);

    const renderer = new VF.Renderer(div, VF.Renderer.Backends.SVG);
    renderer.resize(totalWidth, totalHeight);
    const context = renderer.getContext();

    const timeSig = data.time_signature || [4, 4];
    const beatsPerMeasure = timeSig[0];
    const beatValue = timeSig[1];
    const clef = data.clef || 'treble';

    data.measures.forEach((measure, mIdx) => {
        const lineIdx = Math.floor(mIdx / measuresPerLine);
        const posInLine = mIdx % measuresPerLine;
        const x = leftMargin + posInLine * staveWidth;
        const y = topMargin + lineIdx * staveHeight;

        const stave = new VF.Stave(x, y, staveWidth);
        if (posInLine === 0) stave.addClef(clef);
        if (mIdx === 0) stave.addTimeSignature(`${timeSig[0]}/${timeSig[1]}`);
        stave.setContext(context).draw();

        let tabStave = null;
        if (showTab) {
            tabStave = new VF.TabStave(x, y + tabOffset, staveWidth);
            if (posInLine === 0) tabStave.addTabGlyph();
            tabStave.setContext(context).draw();
            if (posInLine === 0) {
                const conn = new VF.StaveConnector(stave, tabStave);
                conn.setType('singleLeft');
                conn.setContext(context).draw();
            }
        }

        if (!measure.notes || measure.notes.length === 0) return;

        try {
            const vfNotes = measure.notes.map(n => {
                const keys = n.keys && n.keys.length > 0 ? n.keys : ['b/4'];
                let dur = sanitizeDuration(n.duration || 'q');
                if (n.is_rest) return new VF.StaveNote({ keys: [clef === 'treble' ? 'b/4' : 'd/3'], duration: dur });
                const note = new VF.StaveNote({ keys, duration: dur, auto_stem: true });
                keys.forEach((key, ki) => { if (key.includes('#')) note.addModifier(new VF.Accidental('#'), ki); });
                return note;
            });

            const voice = new VF.Voice({ num_beats: beatsPerMeasure, beat_value: beatValue }).setStrict(false);
            voice.addTickables(vfNotes);
            new VF.Formatter().joinVoices([voice]).format([voice], staveWidth - 50);
            voice.draw(context, stave);

            try {
                const beamable = vfNotes.filter(n => !n.isRest() && ['8','16','32'].includes(n.getDuration()));
                if (beamable.length >= 2) VF.Beam.generateBeams(beamable).forEach(b => b.setContext(context).draw());
            } catch (e) { /* beaming can fail */ }

            if (showTab && tabStave) {
                const tabNotes = measure.notes.map(n => {
                    let dur = sanitizeDuration(n.duration || 'q').replace('r', '') || 'q';
                    if (n.is_rest || !n.tab || n.tab.length === 0) return new VF.GhostNote({ duration: dur });
                    return new VF.TabNote({ positions: n.tab, duration: dur });
                });
                const tabVoice = new VF.Voice({ num_beats: beatsPerMeasure, beat_value: beatValue }).setStrict(false);
                tabVoice.addTickables(tabNotes);
                new VF.Formatter().joinVoices([tabVoice]).format([tabVoice], staveWidth - 50);
                tabVoice.draw(context, tabStave);
            }
        } catch (e) {
            context.save(); context.setFont('Arial', 10); context.setFillStyle('#999');
            context.fillText('...', x + staveWidth / 2, y + 50); context.restore();
        }
    });
}

function sanitizeDuration(dur) {
    const map = {
        'w':'w','wr':'wr','h':'h','hr':'hr','hd':'h','hdr':'hr',
        'q':'q','qr':'qr','qd':'q','qdr':'qr',
        '8':'8','8r':'8r','8d':'8','8dr':'8r',
        '16':'16','16r':'16r','32':'32','32r':'32r',
    };
    return map[dur] || 'q';
}

// ─────────────────────────────────────────────
//  Utility
// ─────────────────────────────────────────────
function escHtml(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

// ─────────────────────────────────────────────
//  Processing Log
// ─────────────────────────────────────────────
function showProcessingLog(report) {
    const panel = $('#processing-log');
    if (!panel || !report) return;
    panel.style.display = '';

    const el = id => document.getElementById(id);
    el('log-total-time').textContent = report.total_duration_ms + ' ms';
    el('log-notes-in').textContent = (report.input_metrics || {}).total_notes || '—';
    el('log-notes-out').textContent = (report.output_metrics || {}).total_notes || '—';
    el('log-preset').textContent = report.preset_applied || '—';

    const tbody = panel.querySelector('#log-steps tbody');
    tbody.innerHTML = '';
    (report.steps || []).forEach(step => {
        const tr = document.createElement('tr');
        if (!step.enabled) tr.classList.add('disabled');
        let detail = '';
        if (step.tempo_events_removed) detail += `tempo-${step.tempo_events_removed} `;
        if (step.overlaps_resolved) detail += `overlaps-${step.overlaps_resolved} `;
        if (step.clusters_merged) detail += `clusters-${step.clusters_merged} `;
        if (step.tracks_merged) detail += 'merged ';
        if (step.warnings && step.warnings.length) detail += step.warnings.join('; ');
        tr.innerHTML = `<td>${escHtml(step.name)}</td><td>${step.enabled ? '✓' : '—'}</td>` +
            `<td>${step.duration_ms}</td><td>${step.input_note_count}</td>` +
            `<td>${step.output_note_count}</td><td>${step.notes_removed}</td>` +
            `<td>${escHtml(detail.trim())}</td>`;
        tbody.appendChild(tr);
    });
}

// ─────────────────────────────────────────────
//  Presets
// ─────────────────────────────────────────────
async function loadPresets() {
    try {
        const resp = await fetch('/api/presets');
        const data = await resp.json();
        const sel = $('#cfg-preset');
        if (!sel) return;
        (data.presets || []).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.label;
            opt.dataset.desc = p.description;
            sel.appendChild(opt);
        });
        sel.addEventListener('change', applySelectedPreset);
    } catch (e) { /* presets not critical */ }
}

async function applySelectedPreset() {
    const sel = $('#cfg-preset');
    const descEl = $('#preset-desc');
    if (!sel) return;
    const id = sel.value;
    const opt = sel.selectedOptions[0];
    if (descEl) descEl.textContent = opt?.dataset?.desc || '';
    if (!id) return;
    try {
        const resp = await fetch(`/api/presets/${id}`);
        const data = await resp.json();
        if (data.config) applyConfigToUI(data.config);
    } catch (e) { /* ignore */ }
}

function applyConfigToUI(cfg) {
    if (cfg.filter_noise !== undefined) $('#cfg-filter-noise').checked = cfg.filter_noise;
    if (cfg.min_duration_ticks !== undefined) { $('#cfg-min-duration').value = cfg.min_duration_ticks; updateSliderDisplay('#cfg-min-duration'); }
    if (cfg.min_velocity !== undefined) { $('#cfg-min-velocity').value = cfg.min_velocity; updateSliderDisplay('#cfg-min-velocity'); }
    if (cfg.remove_triplets !== undefined) $('#cfg-remove-triplets').checked = cfg.remove_triplets;
    if (cfg.quantize !== undefined) $('#cfg-quantize').checked = cfg.quantize;
    if (cfg.merge_voices !== undefined) $('#cfg-merge-voices').checked = cfg.merge_voices;
    if (cfg.remove_overlaps !== undefined) $('#cfg-remove-overlaps').checked = cfg.remove_overlaps;
    if (cfg.remove_cc !== undefined) $('#cfg-remove-cc').checked = cfg.remove_cc;
    if (cfg.pitch_cluster) {
        if (cfg.pitch_cluster.enabled !== undefined) $('#cfg-pitch-cluster').checked = cfg.pitch_cluster.enabled;
        if (cfg.pitch_cluster.time_window_ticks !== undefined) { $('#cfg-pitch-cluster-window').value = cfg.pitch_cluster.time_window_ticks; updateSliderDisplay('#cfg-pitch-cluster-window'); }
        if (cfg.pitch_cluster.pitch_threshold !== undefined) { $('#cfg-pitch-cluster-threshold').value = cfg.pitch_cluster.pitch_threshold; updateSliderDisplay('#cfg-pitch-cluster-threshold'); }
    }
    if (cfg.same_pitch_overlap_resolver) {
        if (cfg.same_pitch_overlap_resolver.enabled !== undefined) $('#cfg-same-pitch-overlap').checked = cfg.same_pitch_overlap_resolver.enabled;
    }
}

function updateSliderDisplay(selector) {
    const el = $(selector);
    if (!el) return;
    const disp = el.parentElement.querySelector('.value');
    if (disp) disp.textContent = el.value;
}

async function suggestPreset() {
    try {
        const resp = await fetch('/api/presets/suggest');
        const data = await resp.json();
        if (data.preset_id) {
            const sel = $('#cfg-preset');
            if (sel) {
                sel.value = data.preset_id;
                applySelectedPreset();
            }
        }
    } catch (e) { /* suggestion is best-effort */ }
}

// ─────────────────────────────────────────────
//  Advanced Fields Lock
// ─────────────────────────────────────────────
function initAdvancedToggle() {
    const cb = $('#cfg-lock-advanced');
    if (!cb) return;
    const grid = document.querySelector('.config-grid');
    cb.addEventListener('change', () => {
        if (cb.checked) grid.classList.add('show-advanced');
        else grid.classList.remove('show-advanced');
    });
}

// ─────────────────────────────────────────────
//  LLM Suggestions UI
// ─────────────────────────────────────────────
function updateLLMSuggestionsUI(decisions) {
    const panel = $('#llm-suggestions');
    const list = $('#llm-suggestion-list');
    if (!panel || !list || !decisions || !decisions.length) return;
    panel.style.display = '';
    list.innerHTML = '';
    decisions.forEach(d => {
        const li = document.createElement('li');
        const ok = d.parsed_ok ? '✓' : '✗';
        const changes = d.suggested_changes ? Object.entries(d.suggested_changes).map(([k,v]) => `${k}=${v}`).join(', ') : '—';
        li.textContent = `Call #${d.call_number}: ${ok} ${changes}`;
        list.appendChild(li);
    });
}

// ─────────────────────────────────────────────
//  Initialization
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initSliders();
    initAdvancedToggle();
    loadPresets();

    $('#lang-toggle').addEventListener('click', toggleLanguage);
    $('#btn-process').addEventListener('click', processFile);
    $('#btn-download').addEventListener('click', downloadFile);
    $('#btn-optimize').addEventListener('click', startOptimization);
    $('#btn-apply-optimized').addEventListener('click', applyOptimized);

    const reportBtn = $('#btn-download-report');
    if (reportBtn) reportBtn.addEventListener('click', () => { window.location = '/api/report/download'; });

    // Full player controls
    $('#player-play').addEventListener('click', resumeOrStartFullPlayer);
    $('#player-pause').addEventListener('click', pauseFullPlayer);
    $('#player-stop').addEventListener('click', stopFullPlayerClean);
    $('#player-rewind').addEventListener('click', rewindFullPlayer);
    $('#player-seek').addEventListener('input', e => seekFullPlayer(+e.target.value));

    // Player source toggle
    $('#player-src-original').addEventListener('click', () => {
        state.fullPlayerSource = 'original';
        $('#player-src-original').classList.add('active');
        $('#player-src-processed').classList.remove('active');
        state.fullPlayerData = null;
        stopFullPlayerClean();
    });
    $('#player-src-processed').addEventListener('click', () => {
        if (!state.processed) return;
        state.fullPlayerSource = 'processed';
        $('#player-src-processed').classList.add('active');
        $('#player-src-original').classList.remove('active');
        state.fullPlayerData = null;
        stopFullPlayerClean();
    });
});
