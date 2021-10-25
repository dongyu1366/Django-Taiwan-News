const app = Vue.createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            newsData: null,
            limit: 10,
            offset:0,
        }
    },
    mounted() {
        axios
        .get('/api/news/', {params: {limit: this.limit, offset: this.offset, random: 1}})
        .then(response => (this.newsData = response.data.results))
    },
})

const newList = app.mount("#news-list")
