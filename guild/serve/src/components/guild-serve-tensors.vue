<template>
  <v-data-table
    :items="tensors"
    :headers="headers"
    must-sort
    hide-actions>
    <template slot="items" slot-scope="tensors">
      <td>{{ tensors.item.key }}</td>
      <td>{{ tensors.item.dtype }}</td>
      <td>{{ tensors.item.shape }}</td>
      <td>{{ tensors.item.tensor }}</td>
    </template>
  </v-data-table>
</template>

<script>
export default {
  name: 'guild-select-tensors',

  props: {
    'tensors': {
      type: Array,
      required: true
    }
  },

  data() {
    return {
      headers: [
        { text: 'Key', value: 'key', align: 'left' },
        { text: 'Type', value: 'dtype', align: 'left' },
        { text: 'Shape', value: 'shape', align: 'left' },
        { text: 'Tensor', value: 'tensor', align: 'left' }
      ]
    };
  }
};
</script>
