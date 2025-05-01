<template>
    <div class="live2d_container">
        <canvas ref="liveCanvas"></canvas>
    </div>
</template>

<script setup lang="ts">
import * as PIXI from 'pixi.js';
import { onMounted, ref } from 'vue';
import { Live2DModel } from 'pixi-live2d-display/cubism4';


window.PIXI = PIXI;
const liveCanvas = ref(null);
let app;
let model;
const playMotion = async (group: string, index: number) => {
    if (!model) return
    try {
        await model.motion(group, index)
    } catch (err) {
        console.error(`播放動作失敗: ${group}[${index}]`, err)
    }
}

const playExpression = (expressionName: string) => {
    if (!model) return
    try {
        model.expression(expressionName)
    } catch (err) {
        console.error(`切換表情失敗: ${expressionName}`, err)
    }
}


onMounted(async () => {
    if (!liveCanvas.value) return;

    app = new PIXI.Application({
        view: liveCanvas.value,
        autoStart: true,
        resizeTo: window,
        backgroundAlpha: 0,
    });

    model = await Live2DModel.from('/Haru/Haru.model3.json'); // 模型路徑

    if (!model) {
        console.error("Model faied to load")
        return;
    }
    app.stage.addChild(model);

    // 模型位置與縮放
    model.anchor.set(0.5, 0.5);
    model.scale.set(0.2);
    model.x = window.innerWidth / 2;
    model.y = window.innerHeight / 2;


    //playMotion('TapBody', 2);
    //playExpression("F02");



});
</script>

<style scoped>
canvas {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 1;
}
</style>
