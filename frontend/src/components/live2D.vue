<template>
    <div class="live2d-container" ref="live2dContainerRef">
        <canvas ref="liveCanvasRef"></canvas>
    </div>
</template>

<script setup lang="ts">
import * as PIXI from 'pixi.js';
import { onMounted, ref, onUnmounted, nextTick } from 'vue';
import { Live2DModel } from 'pixi-live2d-display/cubism4';

// 將 PIXI 賦值給 window 對象，某些 Live2D 插件可能需要
(window as any).PIXI = PIXI;

const liveCanvasRef = ref<HTMLCanvasElement | null>(null);
const live2dContainerRef = ref<HTMLDivElement | null>(null);
let app: PIXI.Application | null = null;
let model: Live2DModel | null = null;
let resizeObserver: ResizeObserver | null = null;

const playMotion = async (group: string, index: number) => {
    if (!model) return;
    try {
        await model.motion(group, index);
    } catch (err) {
        console.error(`播放動作失敗: ${group}[${index}]`, err);
    }
};

const playExpression = async (expressionName: string) => {
    if (!model) return;
    try {
        // Live2DModel 的 expression 方法可能不是異步的，
        // 但如果未來版本變更或您使用的特定模型有異步加載表情的行為，
        // 使用 await 可以更安全。如果確定是同步的，可以移除 await。
        await model.expression(expressionName);
    } catch (err) {
        console.error(`切換表情失敗: ${expressionName}`, err);
    }
};

const adjustModelAndRenderer = () => {
    if (app && app.renderer && live2dContainerRef.value && model && model.internalModel) {
        const parentElement = live2dContainerRef.value;
        const newWidth = parentElement.clientWidth;
        const newHeight = parentElement.clientHeight;

        app.renderer.resize(newWidth, newHeight);

        // 更新模型位置使其居中
        model.x = newWidth / 2;
        model.y = newHeight / 2;

        // 重新計算並設置縮放以適應容器，同時保持模型比例
        // 這裡使用 internalModel 的 width 和 height 是為了獲取模型原始（未縮放）的尺寸
        const modelOriginalWidth = model.internalModel.width;
        const modelOriginalHeight = model.internalModel.height;

        if (modelOriginalWidth > 0 && modelOriginalHeight > 0) {
            const scaleX = newWidth / modelOriginalWidth;
            const scaleY = newHeight / modelOriginalHeight;
            const scale = Math.min(scaleX, scaleY) * 0.85; // 乘以一個係數 (例如0.85) 以留出一些邊距
            model.scale.set(scale);
        }
    }
};

onMounted(async () => {
    // 等待 DOM 完全渲染完成
    await nextTick();

    if (!liveCanvasRef.value || !live2dContainerRef.value) {
        console.error("Live2D canvas 或其容器尚未準備好。");
        return;
    }

    const canvasElement = liveCanvasRef.value;
    const containerElement = live2dContainerRef.value;

    try {
        app = new PIXI.Application({
            view: canvasElement,
            autoStart: true,
            width: containerElement.clientWidth, // 使用容器的初始寬度
            height: containerElement.clientHeight, // 使用容器的初始高度
            backgroundAlpha: 0,
            antialias: true, // 抗鋸齒
            resolution: window.devicePixelRatio || 1, // 考慮設備像素比以獲得更清晰的渲染
            autoDensity: true, // 自動調整密度
        });
    } catch (error) {
        console.error("PIXI Application 初始化失敗:", error);
        return;
    }

    try {
        // 請確保您的模型路徑 '/Haru/Haru.model3.json' 是相對於 public 文件夾的正確路徑
        model = await Live2DModel.from('/Haru/Haru.model3.json');
    } catch (error) {
        console.error("Live2D 模型加載失敗:", error);
        if (app) {
            app.destroy(true, { children: true, texture: true, baseTexture: true });
            app = null;
        }
        return;
    }

    if (!model) {
        console.error("模型未能成功初始化。");
        if (app) {
            app.destroy(true, { children: true, texture: true, baseTexture: true });
            app = null;
        }
        return;
    }

    app.stage.addChild(model);

    // 模型錨點設置為中心
    model.anchor.set(0.5, 0.5);

    // 初始調整
    adjustModelAndRenderer();

    // 使用 ResizeObserver 監聽容器大小變化
    if (containerElement) {
        resizeObserver = new ResizeObserver(adjustModelAndRenderer);
        resizeObserver.observe(containerElement);
    }


    // 可選：初始播放動作或表情
    // playMotion('Idle', 0); // 例如：播放一個名為 'Idle' 的動作組中的第一個動作
    // playExpression('F01');
});

onUnmounted(() => {
    if (resizeObserver && live2dContainerRef.value) {
        resizeObserver.unobserve(live2dContainerRef.value);
        resizeObserver.disconnect();
    }
    if (app) {
        // 徹底銷毀 PIXI 應用和相關資源
        app.destroy(true, { children: true, texture: true, baseTexture: true });
        app = null;
        model = null; // 清除模型引用
    }
});
</script>

<style scoped>
.live2d-container {
    width: 100%;
    /* 佔滿 .live2d-panel 的寬度 */
    height: 100%;
    /* 佔滿 .live2d-panel 的高度 */
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    /* 確保模型不會溢出容器 */
}

canvas {
    /* canvas 的大小將由 PIXI Application 控制 */
    max-width: 100%;
    max-height: 100%;
    display: block;
    /* 避免 canvas 底部出現小間隙 */
}
</style>