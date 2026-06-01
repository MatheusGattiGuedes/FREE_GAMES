// let allGames = []
// let storeFilter = "all"

// function render(){

// const container = document.getElementById("games")

// const search = document.getElementById("search").value.toLowerCase()

// container.innerHTML = ""

// allGames
// .filter(g => storeFilter === "all" || g.store === storeFilter)
// .filter(g => g.title.toLowerCase().includes(search))
// .forEach(game => {

// const card = document.createElement("div")

// card.className = "card"

// let timer = ""

// if(game.end){

// const end = new Date(game.end)

// timer = `<p>Ends: ${end.toLocaleDateString()}</p>`

// }

// card.innerHTML = `
// <img src="${game.image}">
// <div class="card-body">
// <h3>${game.title}</h3>

// <div class="badge">${game.store}</div>

// ${timer}

// <a href="${game.url}" target="_blank">Get Game</a>

// </div>
// `

// container.appendChild(card)

// })

// }

// function filterStore(store){

// storeFilter = store

// render()

// }

// document.getElementById("search").addEventListener("input", render)

// fetch("games.json")
// .then(r => r.json())
// .then(data => {

// allGames = [
// ...data.free_now.map(g => ({...g, status:"Free Now"})),
// ...data.next_week.map(g => ({...g, status:"Coming Soon"}))
// ]

// render()

// })

let allGames = []
let storeFilter = "all"

function render() {
    const container = document.getElementById("games")
    const search = document.getElementById("search").value.toLowerCase()

    container.innerHTML = ""

    allGames
        .filter(g => storeFilter === "all" || g.store === storeFilter)
        .filter(g => g.title.toLowerCase().includes(search))
        // .forEach(game => {

        //     const card = document.createElement("div")
        //     card.className = "card"

        //     let timer = ""
        //     if(game.end){
        //         const end = new Date(game.end)
        //         timer = `<p>Ends: ${end.toLocaleDateString()}</p>`
        //     }

        //     // Bloco novo para renderizar os preços (riscando o original se houver desconto)
        //     let prices = ""
        //     if (game.original_price && game.discount_price) {
        //         if (game.discount_price === "0") {
        //             prices = `<p><s>${game.original_price}</s> <strong>GRÁTIS</strong></p>`
        //         } else {
        //             prices = `<p><s>${game.original_price}</s> <strong>${game.discount_price}</strong></p>`
        //         }
        //     }

        //     card.innerHTML = `
        //         <img src="${game.image}">
        //         <div class="card-body">
        //             <h3>${game.title}</h3>
        //             <div class="badge">${game.store}</div>

        //             ${prices}
        //             ${timer}

        //             <a href="${game.url}" target="_blank">Get Game</a>
        //         </div>
        //     `

        //     container.appendChild(card)
        // })
        //     .forEach(game => {
        //         const card = document.createElement("div")
        //         card.className = "card"

        //         // Transforma o card inteiro em um link
        //         card.onclick = () => window.open(game.url, "_blank")

        //         let timer = ""
        //         if (game.end) {
        //             const end = new Date(game.end)
        //             timer = `<p class="date-info">Expira: ${end.toLocaleDateString()}</p>`
        //         } else if (game.start) {
        //             const start = new Date(game.start)
        //             timer = `<p class="date-info">Começa: ${start.toLocaleDateString()}</p>`
        //         }

        //         // O HTML do card focado apenas no título e na data
        //         card.innerHTML = `
        //     <div class="badge">${game.store}</div>
        //     <img src="${game.image}" alt="Capa de ${game.title}">
        //     <div class="card-body">
        //         <h3>${game.title}</h3>
        //         ${timer}
        //     </div>
        // `

        //         container.appendChild(card)
        //     })
        .forEach(game => {
            const card = document.createElement("div")
            card.className = "card"

            let timer = ""

            // Lógica para separar os ativos dos futuros
            if (game.end) {
                // const end = new Date(game.end)
                // timer = `<p class="date-info">Expira: ${end.toLocaleDateString()}</p>`

                // É um jogo ativo: adiciona o clique e a classe de animação/cursor
                card.onclick = () => window.open(game.url, "_blank")
                card.classList.add("clickable")

            } else if (game.start) {
                // const start = new Date(game.start)
                // timer = `<p class="date-info">Começa: ${start.toLocaleDateString()}</p>`

                // Sendo um jogo futuro, ele NÃO recebe o onclick nem a classe .clickable
            } else if (game.store === "Steam") {
                card.onclick = () => window.open(game.url, "_blank")
                card.classList.add("clickable")
            }

            const statusBadge = `<div style="font-size: 0.8em; color: gray;">${game.status}</div>`

            // HTML do card limpo (sem a lógica de preços já que é tudo grátis)
            card.innerHTML = `
                <div class="badge">${game.store}</div>
                <img src="${game.image}" alt="Capa de ${game.title}">
                <div class="card-body">
                    <h3>${game.title}</h3>
                    ${timer}
                </div>
            `

            container.appendChild(card)
        })
}

function filterStore(store) {
    storeFilter = store
    render()
}

document.getElementById("search").addEventListener("input", render)

fetch("games.json")
    .then(r => r.json())
    .then(data => {
        allGames = [
            // AQUI FOI CORRIGIDO: de data.free_now para data.promotions_now
            ...data.promotions_now.map(g => ({ ...g, status: "Promotions Now" })),
            ...data.next_week.map(g => ({ ...g, status: "Coming Soon" }))
        ]

        render()
    })
    .catch(error => console.error("Erro ao carregar o JSON:", error))