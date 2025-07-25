<template>
    <div class="live2d-container" ref="live2dContainerRef">
        <canvas ref="liveCanvasRef"></canvas>
    </div>
</template>

<script setup lang="ts">
import * as PIXI from 'pixi.js';
import { onMounted, ref, onUnmounted, nextTick, watch } from 'vue';
import { Live2DModel } from 'pixi-live2d-display/cubism4';

// 將 PIXI 附加到 window 物件上，這是 pixi-live2d-display 的要求
(window as any).PIXI = PIXI;

// 定義元件的 props，接收來自父元件的模型名稱
const props = defineProps({
    modelName: {
        type: String,
        required: true,
    },
});

const liveCanvasRef = ref<HTMLCanvasElement | null>(null);
const live2dContainerRef = ref<HTMLDivElement | null>(null);

// 將 app 和 model 宣告在元件作用域內，以便在不同函式間共用
let app: PIXI.Application | null = null;
let model: Live2DModel | null = null;
let resizeObserver: ResizeObserver | null = null;

/**
 * 調整模型大小與渲染器尺寸，以適應容器變化
 */
const adjustModelAndRenderer = () => {
    if (app && app.renderer && live2dContainerRef.value && model && model.internalModel) {
        const parentElement = live2dContainerRef.value;
        const newWidth = parentElement.clientWidth;
        const newHeight = parentElement.clientHeight;

        app.renderer.resize(newWidth, newHeight);

        model.x = newWidth / 2;
        model.y = newHeight / 2;

        const modelOriginalWidth = model.internalModel.width;
        const modelOriginalHeight = model.internalModel.height;

        if (modelOriginalWidth > 0 && modelOriginalHeight > 0) {
            const scaleX = newWidth / modelOriginalWidth;
            const scaleY = newHeight / modelOriginalHeight;
            const scale = Math.min(scaleX, scaleY) * 0.85;
            model.scale.set(scale);
        }
    }
};


/**
 * 核心函式：切換或初始化 Live2D 模型
 * @param modelName 要載入的模型名稱
 */
const switchModel = async (modelName: string) => {
    if (!app) {
        console.error("PIXI Application 尚未初始化。");
        return;
    }

    // 如果當前已有模型，則從舞台移除並銷毀
    if (model) {
        app.stage.removeChild(model);
        model.destroy();
        model = null;
    }

    // 根據模型名稱建立模型檔案路徑
    const modelPath = `/${modelName}/${modelName}.model3.json`;

    try {
        // 載入新模型
        model = await Live2DModel.from(modelPath);
    } catch (error) {
        console.error(`Live2D 模型 '${modelName}' 載入失敗:`, error);
        return;
    }

    // 將新模型加入舞台並設定
    app.stage.addChild(model);
    model.anchor.set(0.5, 0.5);
    adjustModelAndRenderer();
};


// 監聽 props.modelName 的變化，並在變化時呼叫 switchModel 函式
watch(() => props.modelName, (newModelName) => {
    if (app && newModelName) {
        switchModel(newModelName);
    }
});


onMounted(async () => {
    await nextTick();

    if (!liveCanvasRef.value || !live2dContainerRef.value) {
        console.error("Live2D canvas 或其容器尚未準備好。");
        return;
    }

    const canvasElement = liveCanvasRef.value;
    const containerElement = live2dContainerRef.value;

    try {
        // 初始化 PIXI Application，這個過程只會在元件掛載時執行一次
        app = new PIXI.Application({
            view: canvasElement,
            autoStart: true,
            width: containerElement.clientWidth,
            height: containerElement.clientHeight,
            backgroundAlpha: 0,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        });
    } catch (error) {
        console.error("PIXI Application 初始化失敗:", error);
        return;
    }

    // 載入初始模型
    await switchModel(props.modelName);

    // 設定 ResizeObserver 來監聽容器大小變化
    if (containerElement) {
        resizeObserver = new ResizeObserver(adjustModelAndRenderer);
        resizeObserver.observe(containerElement);
    }
});

onUnmounted(() => {
    // 元件卸載時，清理資源
    if (resizeObserver && live2dContainerRef.value) {
        resizeObserver.unobserve(live2dContainerRef.value);
        resizeObserver.disconnect();
    }
    if (app) {
        app.destroy(true, { children: true, texture: true, baseTexture: true });
        app = null;
        model = null;
    }
});
</script>

<style scoped>
.live2d-container {
    width: 100%;
    /* 強制佔滿父元素的寬度 */
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}

canvas {
    max-width: 100%;
    max-height: 100%;
    display: block;
}
</style>
