<template>
  <div class="file-detail-container">
    <!-- 新的顶部栏 -->
    <div class="file-detail-top-bar">
      <div class="path-bar">
        <router-link :to="{ path: `/project/${projectName}` }"> / {{ projectName }}</router-link>
        / {{ filename }}
      </div>
      <div class="navigation-buttons">
        <button :disabled="isFirstFile" @click="prevFile" class="action-button">上一个</button>
        <button :disabled="isLastFile" @click="nextFile" class="action-button">下一个</button>
      </div>
    </div>
    <!-- 灰色细线 -->
    <div class="path-bar-divider"></div>

    <!-- 灰线以下部分 -->
    <div class="content-container">
      <!-- 左侧文件列表 -->
      <div class="file-list-container">
        <div class="file-list">
          <div v-for="(file, index) in projectFiles" :key="file.id" @click="viewFileDetails(file.id, file.name, index)" class="file-item">
            {{ file.name }}
          </div>
        </div>
      </div>
      <!-- 中间分隔线 -->
      <!-- <div class="divider"></div> -->
      <!-- 中间文件预览区域 -->
      <div class="file-preview-container">
        <!-- 文件预览区域 -->
        <div v-if="previewUrl">
          <div v-if="isTextFile">
            <pre>{{ textContent }}</pre>
          </div>
          <div v-else-if="isImageFile" class="centered-content">
            <img :src="previewUrl" alt="预览图" style="max-width: 100%;">
          </div>
          <div v-else-if="isAudioFile" class="centered-content">
            <audio controls :src="previewUrl"></audio>
          </div>
          <div v-else-if="isVideoFile" class="centered-content">
            <video controls :src="previewUrl" style="max-width: 100%;"></video>
          </div>
          <div v-else-if="isPdfFile">
            <embed :src="previewUrl" type="application/pdf" width="100%" height="600px" />
          </div>
          <div v-else>
            <a :href="previewUrl" download>下载文件</a>
          </div>
        </div>
      </div>
      <!-- 右侧分隔线 -->
      <div class="divider"></div>
      <!-- 右侧解析结果区域 -->
      <div class="analysis-result-container">
        <!-- 这里可以添加解析结果的内容 -->
        <p>解析结果区域</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { ref, onMounted } from 'vue';

export default {
  name: 'FileDetail',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const projectName = route.params.projectname;
    const filename = route.params.filename;
    const currentIndex = parseInt(route.query.index);
    const project = ref(null);
    const previewUrl = ref('');
    const textContent = ref('');
    const isTextFile = ref(false);
    const isImageFile = ref(false);
    const isAudioFile = ref(false);
    const isVideoFile = ref(false);
    const isPdfFile = ref(false); // 新增判断PDF文件的变量
    const projectFiles = ref([]);

    const prevFile = () => {
      if (currentIndex > 0) {
        const prevIndex = currentIndex - 1;
        axios.get(`http://127.0.0.1:8000/api/get_projects/`)
          .then((response) => {
            const projects = response.data.projects;
            project.value = projects.find(p => p.name === projectName);
            if (project.value) {
              const prevFile = project.value.files[prevIndex];
              const path = `/project/${projectName}/${prevFile.name}`;
              router.push({ path, query: { index: prevIndex } });
            }
          })
          .catch((error) => {
            console.error('获取项目文件列表失败:', error);
          });
      }
    };

    const nextFile = () => {
      axios.get(`http://127.0.0.1:8000/api/get_projects/`)
        .then((response) => {
          const projects = response.data.projects;
          project.value = projects.find(p => p.name === projectName);
          if (project.value) {
            const nextIndex = currentIndex + 1;
            if (project.value.files && nextIndex < project.value.files.length) {
              const nextFile = project.value.files[nextIndex];
              const path = `/project/${projectName}/${nextFile.name}`;
              router.push({ path, query: { index: nextIndex } });
            }
          }
        })
        .catch((error) => {
          console.error('获取项目文件列表失败:', error);
        });
    };

    const viewFileDetails = (fileId, filename, index) => {
      const path = `/project/${projectName}/${filename}`;
      router.push({ path, query: { index } });
    };

    const isFirstFile = currentIndex === 0;
    const isLastFile = project.value && project.value.files && currentIndex === project.value.files.length - 1;

    onMounted(() => {
      const fileExtension = filename.split('.').pop().toLowerCase();
      isTextFile.value = ['.txt', '.csv'].includes(`.${fileExtension}`);
      isImageFile.value = ['.jpg', '.jpeg', '.png'].includes(`.${fileExtension}`);
      isAudioFile.value = ['.wav', '.mp3'].includes(`.${fileExtension}`);
      isVideoFile.value = ['.aac', '.mp4'].includes(`.${fileExtension}`);
      isPdfFile.value = ['.pdf'].includes(`.${fileExtension}`); // 判断是否为PDF文件

      axios.get(`http://127.0.0.1:8000/api/get_file_content/${projectName}/${filename}/`, { responseType: 'blob' })
        .then((response) => {
          const url = URL.createObjectURL(response.data);
          previewUrl.value = url;

          if (isTextFile.value) {
            const reader = new FileReader();
            reader.onload = () => {
              textContent.value = reader.result;
            };
            reader.readAsText(response.data);
          }
        })
        .catch((error) => {
          console.error('获取文件内容失败:', error);
        });

      axios.get(`http://127.0.0.1:8000/api/get_project_files/${projectName}/`)
        .then((response) => {
          projectFiles.value = response.data.files;
        })
        .catch((error) => {
          console.error('获取项目文件列表失败:', error);
        });
    });

    return {
      projectName,
      filename,
      prevFile,
      nextFile,
      isFirstFile,
      isLastFile,
      previewUrl,
      textContent,
      isTextFile,
      isImageFile,
      isAudioFile,
      isVideoFile,
      isPdfFile, // 返回新增的变量
      projectFiles,
      viewFileDetails
    };
  }
};
</script>

<style scoped>

.file-detail-container {
  padding: 0px;
}

/* 新的顶部栏样式 */
.file-detail-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
  padding: 10px 20px;
  border-bottom: 1px solid #dee2e6;
}

/* 路径栏样式 */
.path-bar {
  font-size: 14px;
  color: #666;
}

.path-bar a {
  color: #007bff;
  text-decoration: none;
}

.path-bar a:hover {
  text-decoration: underline;
}

/* 导航按钮样式 */
.navigation-buttons {
  display: flex;
}

.action-button {
  padding: 5px 10px;
  margin-left: 10px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 3px;
  cursor: pointer;
}

.action-button:hover {
  background-color: #0056b3;
}

/* 路径栏分隔线 */
.path-bar-divider {
  border-bottom: 1px solid #ccc;
  margin-bottom: 0px;
  width: 100%;
}

/* 灰线以下内容容器 */
.content-container {
  display: flex;
}

/* 左侧文件列表样式 */
.file-list-container {
  width: 20%;
  min-width: 200px;
  border-right: 1px solid #ccc;
  padding: 5px;
}

.file-list {
  list-style-type: none;
  padding: 0;
}

.file-item {
  cursor: pointer;
  padding: 5px;
}

.file-item:hover {
  background-color: #f0f0f0;
}

/* 中间文件预览区域样式 */
.file-preview-container {
  width: 40%;
  position: relative;
  padding: 0px;
  height: 600px;
}

.centered-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

/* 右侧解析结果区域样式 */
.analysis-result-container {
  width: 40%;
  padding: 5px;
}

/* 分隔线样式 */
.divider {
  border-right: 1px solid #ccc;
}
</style>