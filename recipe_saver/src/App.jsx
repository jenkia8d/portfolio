import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [view, setView] = useState('home')
  const [title, setTitle] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [ingredients, setIngredients] = useState('')
  
  const [recipes, setRecipes] = useState(() => {
    const savedRecipes = localStorage.getItem('recipes')
    return savedRecipes ? JSON.parse(savedRecipes) : []
  })

  useEffect(() => {
    localStorage.setItem('recipes', JSON.stringify(recipes))
  }, [recipes])



  function viewRecipes() {
    // alert('View Recipes clicked')
    setView('recipes')
  }

  function addRecipe() {
    // alert('Add Recipe clicked')
    setView('add')
  }

  function saveRecipe() {
  const newRecipe = {
    id: Date.now(),
    title,
    sourceUrl,
    ingredients,
  }

    setRecipes([...recipes, newRecipe])
    setTitle('')
    setSourceUrl('')
    setIngredients('')
    setView('recipes')

    alert('Recipe saved!')

  }



  return (
    <main className="app">
      <section className="hero">
        <h1>Recipe Saver</h1>
        <p>Save recipes from browser tabs into one organized place.</p>
      </section>

      <section className="actions">
        <button type="button" className="action-button" 
        onClick={viewRecipes}
        >
          View Recipes
        </button>

        <button type="button" className="action-button"
        onClick={addRecipe}
        >
          Add Recipe
        </button>
      </section>

      {view === 'home' && <p>Choose an option to get started.</p>}
      {view === 'recipes' && (
        <section className="recipe-list">
          <h2>Saved Recipes</h2>

          {recipes.length === 0 ? (
            <p>No recipes saved yet.</p>
          ) : (
            recipes.map((recipe) => (
              <article key={recipe.id} className="recipe-card">
                <h3>{recipe.title}</h3>
                <p>{recipe.sourceUrl}</p>
                <pre>{recipe.ingredients}</pre>
              </article>
            ))
          )}
        </section>
      )}
      
      {view === 'add' && <p>Recipe form goes here.</p>}
      {view === 'add' && (
        <section className="recipe-form">
          <h2>Add a Recipe</h2>

          <div className="form-field">
            <label htmlFor="title">Title</label>
            <input 
              id="title" 
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="sourceUrl">Source URL</label>
            <input
              id="sourceUrl"
              type="text"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="ingredients">Ingredients</label>
            <textarea
              id="ingredients"
              value={ingredients}
              onChange={(event) => setIngredients(event.target.value)}
              rows="8"
              placeholder="2 eggs&#10;1 cup flour&#10;1/2 cup sugar"
            />
          </div>

          <div>
            <button
              type="button"
              className="action-button"
              onClick={saveRecipe}
            >
              Save Recipe
            </button>
          </div>

        </section>

        
      )}



    </main>
  )
}

export default App
