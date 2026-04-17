import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [view, setView] = useState('home')
  const [title, setTitle] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [ingredients, setIngredients] = useState('')
  const [notes, setNotes] = useState('')
  const [selectedRecipe, setSelectedRecipe] = useState(null)
  const [editingRecipeId, setEditingRecipeId] = useState(null)



  
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

  function openRecipe(recipe) {
    setSelectedRecipe(recipe)
    setView('detail')
  }

  function addRecipe() {
    // alert('Add Recipe clicked')
    setView('add')
  }

  function editRecipe() {
    // alert('Edit Recipe clicked')
    setView('add')
    setEditingRecipeId(selectedRecipe.id)
    setTitle(selectedRecipe.title)
    setSourceUrl(selectedRecipe.sourceUrl)
    setIngredients(selectedRecipe.ingredients)
    setNotes(selectedRecipe.notes)
  }

  function clearRecipes() {
    if (!window.confirm('Are you sure you want to clear all recipes?')) {
      return
    }

    localStorage.removeItem('recipes')
    setRecipes([])
    setSelectedRecipe(null)
    setEditingRecipeId(null)
    setView('recipes')
  }



  function saveRecipe() {
  const recipeData = {
    id: editingRecipeId ?? Date.now(),
    title,
    sourceUrl,
    ingredients,
    notes,
  }

  if (editingRecipeId) {
    const updatedRecipes = recipes.map((recipe) =>
      recipe.id === editingRecipeId ? recipeData : recipe
    )

    setRecipes(updatedRecipes)
    setSelectedRecipe(recipeData)
  } else {
    setRecipes([...recipes, recipeData])
  }

    setTitle('')
    setSourceUrl('')
    setIngredients('')
    setNotes('')
    setEditingRecipeId(null)
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
          <div className="recipe-view-list">
          {recipes.length === 0 ? (
            <p>No recipes saved yet.</p>
          ) : (
            recipes.map((recipe) => (
              <article key={recipe.id} className="recipe-card">
                <button type="button" className="recipe-name-button" onClick={() => openRecipe(recipe)}>
                  {recipe.title}
                </button>
                {/* <h3>{recipe.title}</h3> */}
                {/* <p>{recipe.sourceUrl}</p> */}
                {/* <pre>{recipe.ingredients}</pre> */}
                {/* <pre>{recipe.notes}</pre> */}
              </article>
            ))
          )}
          </div>
      
          <div className="recipe-view-actions">
          <button type="button" className="action-button" onClick={clearRecipes}>
            Clear Recipes
          </button>
          </div>


        </section>
      )}

      {view === 'detail' && selectedRecipe && (
        <section className="recipe-detail">
          <h2>{selectedRecipe.title}</h2>
          <a
            href={selectedRecipe.sourceUrl}
            target="_blank"
            rel="noreferrer"
          >
            {selectedRecipe.sourceUrl}
          </a>

          <h3>{'Ingredients'}</h3>
          {/* <pre>{selectedRecipe.ingredients}</pre>
          <pre>{selectedRecipe.notes}</pre> */}
          
          <ol>
            {selectedRecipe.ingredients
              .split('\n')
              .filter((item) => item.trim() !== '')
              .map((item, index) => (
                <li key={index}>{item}</li>
              ))}
          </ol>
          <h3>{'Notes'}</h3>
          <ol>
            {selectedRecipe.notes
              .split('\n')
              .filter((item) => item.trim() !== '')
              .map((item, index) => (
                <li key={index}>{item}</li>
              ))}
          </ol>


        
          <div className="recipe-detail-actions">
              <button
                type="button"
                className="action-button"
                onClick={editRecipe}
              >
                Edit Recipe
              </button>
          </div>
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

          <div className="form-field">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows="8"
              placeholder="Notes"
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
